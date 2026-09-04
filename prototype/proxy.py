"""
CapOrches Framework-Agnostic Multi-Agent Interception Proxy (§4.3.3, Requirement R9).

Provides an OpenAI-compatible HTTP reverse proxy (AgentOpt pattern, Hua et al., 2026)
that intercepts outbound LLM API requests from agent frameworks (LangGraph, AutoGen,
CrewAI, DSPy). Requests supply task metadata and SLA floors via HTTP headers
(e.g., X-CapOrches-Task-ID, X-CapOrches-Workflow-ID), and the proxy routes prompts
to provisioned worker instances according to the Level 1 allocation routing table.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from poc.formulation.types import TaskId
from prototype.loop import AssignmentRegistry

logger = logging.getLogger("caporches.proxy")


class CapOrchesProxyHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler implementing OpenAI v1 API compatibility with routing."""

    # Injected by CapOrchesProxy
    assignment_registry: AssignmentRegistry | None = None
    backend_urls: dict[str, str] = {}
    default_profile: str = "default-profile"

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy standard server logging in production/tests
        logger.debug("%s - - [%s] %s", self.client_address[0],
                     self.log_date_time_string(), format % args)

    def do_GET(self) -> None:
        if self.path == "/health":
            self._handle_health()
        elif self.path in ("/v1/models", "/models"):
            self._handle_models()
        else:
            self._send_json(404, {"error": {"message": f"Endpoint {self.path} not found", "type": "invalid_request_error"}})

    def do_POST(self) -> None:
        if self.path in ("/v1/chat/completions", "/chat/completions"):
            self._handle_chat_completions()
        else:
            self._send_json(404, {"error": {"message": f"Endpoint {self.path} not found", "type": "invalid_request_error"}})

    def _handle_health(self) -> None:
        response = {
            "status": "healthy",
            "service": "caporches-proxy",
            "version": "1.0.0",
            "active_allocation": bool(self.assignment_registry and self.assignment_registry.versions),
        }
        self._send_json(200, response)

    def _handle_models(self) -> None:
        models: list[dict[str, Any]] = []
        if self.assignment_registry and self.assignment_registry.versions:
            active = self.assignment_registry.active
            for profile_id in active.provisioning:
                models.append({
                    "id": profile_id,
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "caporches",
                })
        if not models:
            models.append({
                "id": self.default_profile,
                "object": "model",
                "created": int(time.time()),
                "owned_by": "caporches",
            })

        self._send_json(200, {"object": "list", "data": models})

    def _handle_chat_completions(self) -> None:
        start_time = time.perf_counter()
        content_length = int(self.headers.get("Content-Length", 0))
        body_bytes = self.rfile.read(content_length)

        try:
            payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
        except Exception:
            self._send_json(400, {"error": {"message": "Invalid JSON payload", "type": "invalid_request_error"}})
            return

        # Extract Header-based Task Metadata (Requirement R9)
        task_header = self.headers.get("X-CapOrches-Task-ID")
        workflow_header = self.headers.get("X-CapOrches-Workflow-ID", "wf-default")
        rel_floor_header = self.headers.get("X-CapOrches-Rel-Floor")
        lat_ceil_header = self.headers.get("X-CapOrches-Lat-Ceil")

        # Resolve TaskId
        target_task_id: TaskId | None = None
        if task_header:
            if "/" in task_header:
                parts = task_header.split("/", 1)
                target_task_id = TaskId(parts[0], parts[1])
            else:
                target_task_id = TaskId(workflow_header, task_header)

        # Query Level 1 Routing Table
        routed_profile = self.default_profile

        if self.assignment_registry and self.assignment_registry.versions:
            try:
                active = self.assignment_registry.active
                if target_task_id and target_task_id in active.routing:
                    routed_profile = active.routing[target_task_id]
                elif target_task_id:
                    # Match by task_name across workflows
                    for tid, prof in active.routing.items():
                        if tid.task_name == target_task_id.task_name:
                            routed_profile = prof
                            break
                elif "model" in payload and payload["model"] in active.provisioning:
                    routed_profile = payload["model"]
            except Exception as e:
                logger.warning("Routing lookup error: %s", e)

        # Backend Dispatch or Synthetic Emulation
        backend_url = self.backend_urls.get(routed_profile)
        if backend_url:
            self._forward_to_backend(backend_url, body_bytes, routed_profile, start_time, target_task_id)
        else:
            self._synthesize_response(payload, routed_profile, start_time, target_task_id)

    def _forward_to_backend(self,
                             backend_url: str,
                             body_bytes: bytes,
                             routed_profile: str,
                             start_time: float,
                             target_task_id: TaskId | None) -> None:
        """Forwards request to provisioned physical serving instance (vLLM / TGI)."""
        req = Request(
            f"{backend_url.rstrip('/')}/v1/chat/completions",
            data=body_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(req, timeout=30.0) as resp:
                resp_data = resp.read()
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                extra_headers = {
                    "X-CapOrches-Routed-Profile": routed_profile,
                    "X-CapOrches-Latency-Ms": f"{elapsed_ms:.2f}",
                }
                if target_task_id:
                    extra_headers["X-CapOrches-Task-ID"] = target_task_id.task_name
                    extra_headers["X-CapOrches-Workflow-ID"] = target_task_id.workflow_id
                self._send_bytes(resp.status, resp_data, extra_headers)
        except URLError as e:
            self._send_json(502, {
                "error": {
                    "message": f"CapOrches worker dispatch failed: {e}",
                    "type": "bad_gateway",
                    "routed_profile": routed_profile,
                }
            })

    def _synthesize_response(self,
                             payload: dict[str, Any],
                             routed_profile: str,
                             start_time: float,
                             target_task_id: TaskId | None) -> None:
        """Generates OpenAI-compliant chat completion response when running standalone."""
        messages = payload.get("messages", [])
        last_prompt = messages[-1].get("content", "") if messages else ""
        created_ts = int(time.time())
        completion_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        response_payload = {
            "id": completion_id,
            "object": "chat.completion",
            "created": created_ts,
            "model": routed_profile,
            "system_fingerprint": "caporches-proxy-v1",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": f"[CapOrches Route: {routed_profile}] Processed prompt: {last_prompt[:50]!r}",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": max(1, len(last_prompt) // 4),
                "completion_tokens": 16,
                "total_tokens": max(1, len(last_prompt) // 4) + 16,
            },
        }

        extra_headers = {
            "X-CapOrches-Routed-Profile": routed_profile,
            "X-CapOrches-Latency-Ms": f"{elapsed_ms:.2f}",
        }
        if target_task_id:
            extra_headers["X-CapOrches-Task-ID"] = target_task_id.task_name
            extra_headers["X-CapOrches-Workflow-ID"] = target_task_id.workflow_id

        self._send_json(200, response_payload, extra_headers)

    def _send_json(self, status: int, data: dict[str, Any], extra_headers: dict[str, str] | None = None) -> None:
        body = json.dumps(data).encode("utf-8")
        headers = {"Content-Type": "application/json", "Content-Length": str(len(body))}
        if extra_headers:
            headers.update(extra_headers)
        self._send_bytes(status, body, headers)

    def _send_bytes(self, status: int, body: bytes, headers: dict[str, str]) -> None:
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)


class CapOrchesProxy:
    """Manages the lifecycle of the CapOrches OpenAI reverse proxy server."""

    def __init__(self,
                 host: str = "127.0.0.1",
                 port: int = 8000,
                 assignment_registry: AssignmentRegistry | None = None,
                 backend_urls: dict[str, str] | None = None,
                 default_profile: str = "default-profile") -> None:
        self.host = host
        self.port = port
        self.assignment_registry = assignment_registry
        self.backend_urls = backend_urls or {}
        self.default_profile = default_profile
        self.server: ThreadingHTTPServer | None = None
        self._thread: Thread | None = None

    def start(self, blocking: bool = False) -> None:
        handler_cls = type("ConfiguredProxyHandler", (CapOrchesProxyHandler,), {
            "assignment_registry": self.assignment_registry,
            "backend_urls": self.backend_urls,
            "default_profile": self.default_profile,
        })
        self.server = ThreadingHTTPServer((self.host, self.port), handler_cls)
        # Handle port 0 dynamic assignment
        self.port = self.server.server_address[1]

        if blocking:
            self.server.serve_forever()
        else:
            self._thread = Thread(target=self.server.serve_forever, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def __enter__(self) -> CapOrchesProxy:
        self.start(blocking=False)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="CapOrches OpenAI-compatible Framework Interception Proxy")
    parser.add_argument("--host", default="127.0.0.1", help="Host address to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    args = parser.parse_args()

    proxy = CapOrchesProxy(host=args.host, port=args.port)
    print(f"Starting CapOrches Framework Proxy on http://{args.host}:{args.port}")
    try:
        proxy.start(blocking=True)
    except KeyboardInterrupt:
        print("\nStopping CapOrches Framework Proxy...")
        proxy.stop()


if __name__ == "__main__":
    main()
