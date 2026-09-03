"""
J1 — Workflow Ingestion. Parse, validate, freeze a batch (§2.3, §3.1).

Outside PoC scope — see prototype/README.md. Owner: 035.

Reads `data/eval_batches/eval_batch_3workflows.json`, which is real: three concurrent
incident-detection workflows derived from multi-host Zookeeper logs, four tasks each.

WHAT THE MANIFEST DOES NOT CARRY, WHICH IS ITSELF WORTH KNOWING

The v2 formulation needs three per-task parameters (§1.3):

    load(t)      throughput demand
    R_min(t)     reliability floor
    L_max(t)     latency ceiling

The batch manifest has **none of them**. Its nodes carry only `id` and `task_type`. That is
not a defect in the file — it predates the v2 formulation — but it means the existing
evaluation batch cannot be fed to the optimizer without additional input, and nothing in the
architecture says where those values come from. §2.4's data flow lists "Batch manifest" as
the input to J1 and "Frozen task graphs" as the output, with no mention of demand.

**This is a gap for 083 and 035:** either the manifest format grows three fields per node, or
a separate workload specification is introduced and §2.4 documents it. Here the second is
assumed, via `TaskTypeSpec`, so the loop can run — but the choice belongs to the team.

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
    """The per-task-type demand the manifest does not carry. [PROPOSED]"""

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
           type_specs: dict[str, TaskTypeSpec]) -> Batch:
    """Parse, validate and freeze. Completion condition: all workflows parsed (§3.1 J1)."""
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
            if task_type not in type_specs:
                raise InvalidBatch(
                    f"{workflow_id}/{node['id']}: no demand specified for task type "
                    f"{task_type!r}. The manifest carries no load or floors; see this "
                    f"module's docstring.")

            successors = tuple(
                TaskId(workflow_id, other["id"]) for other in nodes
                if node["id"] in other.get("depends_on", []))

            for dependency in node.get("depends_on", []):
                if dependency not in declared:
                    raise InvalidBatch(
                        f"{workflow_id}/{node['id']} depends on unknown node "
                        f"{dependency!r}")

            spec = type_specs[task_type]
            tasks.append(Task(
                id=TaskId(workflow_id, node["id"]),
                task_type=task_type,
                load=spec.load,
                rel_floor=spec.rel_floor,
                lat_ceil=spec.lat_ceil,
                successors=successors,
            ))

    if not tasks:
        raise InvalidBatch("batch contains no tasks")

    # Frozen after ingestion: structure is immutable (principle P8).
    return Batch(batch_id=data.get("batch_id", "unnamed"),
                 tasks=tuple(tasks),
                 workflow_ids=tuple(workflow_ids))
