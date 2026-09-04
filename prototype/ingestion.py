"""
J1 — Workflow Ingestion. Parse, validate, freeze a batch (§2.3, §3.1).

Outside PoC scope — see prototype/README.md. Owner: 035 / 083.

Reads `data/eval_batches/eval_batch_3workflows.json`: three concurrent
incident-detection workflows derived from multi-host Zookeeper logs, four tasks each.

UNIFIED MANIFEST SCHEMA RATIFICATION (§1.3, resolving the 083/035 gap):
The v2 formulation requires three per-task parameters:
    load(t)      throughput demand
    rel_floor(t) reliability floor
    lat_ceil(t)  latency ceiling

The batch manifest natively carries these parameters on each DAG node. For backward
compatibility and scenario exploration (e.g. strict floor injection), `type_specs` may
optionally be passed to provide default values or overrides. If a node lacks demand and
no spec is provided, J1 fails loudly (InvalidBatch).

Precedence is parsed and carried on `Task.successors`, and is used for execution ordering
only. It does not enter the optimisation (§1.9, and settled in CLAUDE.md).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from poc.formulation.types import Task, TaskId


@dataclass(frozen=True)
class TaskTypeSpec:
    """Optional per-task-type demand override / fallback specification."""

    load: float
    rel_floor: float
    lat_ceil: float


class InvalidBatch(Exception):
    """The batch is malformed. J1 fails loudly rather than emitting a partial graph."""


@dataclass(frozen=True)
class Batch:
    batch_id: str
    tasks: tuple[Task, ...]
    workflow_ids: tuple[str, ...]

    def as_list(self) -> list[Task]:
        return list(self.tasks)


def ingest(manifest_path: str | Path,
           type_specs: dict[str, TaskTypeSpec] | None = None) -> Batch:
    """Parse, validate and freeze. Completion condition: all workflows parsed (§3.1 J1).

    Each DAG node may embed 'load', 'rel_floor', and 'lat_ceil' directly.
    If type_specs is provided, it can supply fallback specifications or overrides.
    """
    data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))

    if "workflows" not in data:
        raise InvalidBatch("manifest has no 'workflows' key")

    tasks: list[Task] = []
    workflow_ids: list[str] = []

    for workflow in data["workflows"]:
        workflow_id = workflow.get("workflow_id")
        if not workflow_id:
            raise InvalidBatch("a workflow has no workflow_id")
        workflow_ids.append(workflow_id)

        nodes = workflow.get("dag", {}).get("nodes")
        if not nodes:
            raise InvalidBatch(f"{workflow_id} has no dag.nodes")

        declared = {node["id"] for node in nodes}
        for node in nodes:
            task_type = node.get("task_type")
            if not task_type:
                raise InvalidBatch(f"{workflow_id}/{node.get('id')}: node missing task_type")

            # Check if type_specs explicitly overrides or supplies demand
            spec = type_specs.get(task_type) if type_specs else None
            load = spec.load if spec is not None else node.get("load")
            rel_floor = spec.rel_floor if spec is not None else node.get("rel_floor")
            lat_ceil = spec.lat_ceil if spec is not None else node.get("lat_ceil")

            if load is None or rel_floor is None or lat_ceil is None:
                raise InvalidBatch(
                    f"{workflow_id}/{node['id']}: no demand specified for task type "
                    f"{task_type!r}. The manifest node does not embed load/rel_floor/lat_ceil "
                    f"and no matching TaskTypeSpec was provided.")

            successors = tuple(
                TaskId(workflow_id, other["id"]) for other in nodes
                if node["id"] in other.get("depends_on", []))

            for dependency in node.get("depends_on", []):
                if dependency not in declared:
                    raise InvalidBatch(
                        f"{workflow_id}/{node['id']} depends on unknown node "
                        f"{dependency!r}")

            tasks.append(Task(
                id=TaskId(workflow_id, node["id"]),
                task_type=task_type,
                load=float(load),
                rel_floor=float(rel_floor),
                lat_ceil=float(lat_ceil),
                successors=successors,
            ))

    if not tasks:
        raise InvalidBatch("batch contains no tasks")

    # Frozen after ingestion: structure is immutable (principle P8).
    return Batch(batch_id=data.get("batch_id", "unnamed"),
                 tasks=tuple(tasks),
                 workflow_ids=tuple(workflow_ids))

