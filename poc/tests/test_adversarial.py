"""
T2 fixtures — hand-built cases where greedy ordering misleads.

Spec: docs/System_Architecture_v2.md §6.6; CLAUDE.md ground-truth instance.
Covers build steps 4 and 9. Owner: 035

Two assertions on adversarial_3t2p, and they are the checkpoints for two different build
steps — keep them separate rather than merging into one test:

    step 4  exact_milp returns 280, routing {t1→m2, t2→m2, t3→m1}, n = {m1:1, m2:1}
    step 9  track_a_greedy returns 300

The second is not a bug being tolerated. Greedy returning 300 is the T2 result — if it
returns 280, the myopia is not being reproduced and something is wrong with either the
fixture or cost_to_admit.
"""
import pytest

pytestmark = pytest.mark.skip(reason="build steps 4 and 9 not yet implemented")
