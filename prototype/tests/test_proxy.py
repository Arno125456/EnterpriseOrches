"""
Tests for CapOrches Framework Interception Proxy (§4.3.3, Requirement R9).
"""

from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from poc.formulation.types import AllocationResult, TaskId
from prototype.loop import AssignmentRegistry
from prototype.proxy import CapOrchesProxy


@pytest.fixture
def running_proxy():
    """Starts a proxy server on an ephemeral port and cleanly shuts it down."""
    registry = AssignmentRegistry()
    alloc = AllocationResult(
        routing={
            TaskId("wf-1", "triage"): "profile-t4",
            TaskId("wf-1", "synthesis"): "profile-a100",
        },
        provisioning={"profile-t4": 2, "profile-a100": 1},
        total_cost=320.0,
        gpus_used=6,
        strategy="TEST",
        lower_bound=300.0,
        compute_time=0.01,
        feasible=True,
    )
    registry.persist(alloc)

    proxy = CapOrchesProxy(host="127.0.0.1", port=0, assignment_registry=registry)
    proxy.start(blocking=False)
    yield proxy
    proxy.stop()


def test_proxy_health_endpoint(running_proxy):
    url = f"http://127.0.0.1:{running_proxy.port}/health"
    with urlopen(url, timeout=5.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "healthy"
        assert data["service"] == "caporches-proxy"
        assert data["active_allocation"] is True


def test_proxy_models_endpoint(running_proxy):
    url = f"http://127.0.0.1:{running_proxy.port}/v1/models"
    with urlopen(url, timeout=5.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["object"] == "list"
        model_ids = {m["id"] for m in data["data"]}
        assert "profile-t4" in model_ids
        assert "profile-a100" in model_ids


def test_proxy_chat_completions_routing_via_task_headers(running_proxy):
    url = f"http://127.0.0.1:{running_proxy.port}/v1/chat/completions"
    payload = {
        "model": "gpt-4o",  # Framework model name to be intercepted and overridden
        "messages": [
            {"role": "system", "content": "You are a code synthesis assistant."},
            {"role": "user", "content": "Refactor the knapsack DP loop."},
        ],
    }
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-CapOrches-Task-ID": "synthesis",
            "X-CapOrches-Workflow-ID": "wf-1",
            "X-CapOrches-Rel-Floor": "0.95",
            "X-CapOrches-Lat-Ceil": "150.0",
        },
        method="POST",
    )

    with urlopen(req, timeout=5.0) as resp:
        assert resp.status == 200
        assert resp.headers.get("X-CapOrches-Routed-Profile") == "profile-a100"
        assert resp.headers.get("X-CapOrches-Task-ID") == "synthesis"
        assert resp.headers.get("X-CapOrches-Workflow-ID") == "wf-1"
        assert float(resp.headers.get("X-CapOrches-Latency-Ms", "0")) >= 0.0

        data = json.loads(resp.read().decode("utf-8"))
        assert data["object"] == "chat.completion"
        assert data["model"] == "profile-a100"
        assert "profile-a100" in data["choices"][0]["message"]["content"]
        assert data["usage"]["total_tokens"] > 0


def test_proxy_chat_completions_compound_task_id(running_proxy):
    url = f"http://127.0.0.1:{running_proxy.port}/v1/chat/completions"
    payload = {
        "messages": [{"role": "user", "content": "Triage incident log #401"}],
    }
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-CapOrches-Task-ID": "wf-1/triage",
        },
        method="POST",
    )

    with urlopen(req, timeout=5.0) as resp:
        assert resp.status == 200
        assert resp.headers.get("X-CapOrches-Routed-Profile") == "profile-t4"
        data = json.loads(resp.read().decode("utf-8"))
        assert data["model"] == "profile-t4"


def test_proxy_chat_completions_default_fallback(running_proxy):
    url = f"http://127.0.0.1:{running_proxy.port}/v1/chat/completions"
    payload = {
        "messages": [{"role": "user", "content": "Unmanaged request"}],
    }
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(req, timeout=5.0) as resp:
        assert resp.status == 200
        assert resp.headers.get("X-CapOrches-Routed-Profile") == "default-profile"


def test_proxy_invalid_json(running_proxy):
    url = f"http://127.0.0.1:{running_proxy.port}/v1/chat/completions"
    req = Request(
        url,
        data=b"invalid non json string",
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with pytest.raises(HTTPError) as exc_info:
        urlopen(req, timeout=5.0)
    assert exc_info.value.code == 400


def test_proxy_unknown_endpoint(running_proxy):
    url = f"http://127.0.0.1:{running_proxy.port}/unknown"
    with pytest.raises(HTTPError) as exc_info:
        urlopen(url, timeout=5.0)
    assert exc_info.value.code == 404
