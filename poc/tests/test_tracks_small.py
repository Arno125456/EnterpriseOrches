"""
Each track vs the exact optimum by exhaustion, on instances ≤ 8 tasks, ≤ 4 profiles. Bound tests for B and C: bound ≤ true optimum always; record whether B_bound ≥ C_bound (that is T1).

Spec: docs/System_Architecture_v2.md §6.6.
Covers build step 7. Owner: 089
"""
import pytest

pytestmark = pytest.mark.skip(reason="build step 7 not yet implemented")
