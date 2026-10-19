import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "lab"))
import build_site


def fake(n, k):
    return [{"id": str(i), "p_reply": 1 - i / n, "outcome": "positive_reply" if i < k else "silent", "source": "backfill-blind"}
            for i in range(n)]


def test_calibration_with_a_small_ledger_does_not_divide_by_zero(monkeypatch):
    """Under 10 scored sends the top-10% bucket was empty and len(b) == 0 raised ZeroDivisionError,
    so the page could not be built for a new product's first handful of sends."""
    monkeypatch.setattr(build_site, "joined", lambda: fake(6, 1))
    c = build_site.calibration_rows()
    assert c["n"] == 6 and c["k"] == 1
    assert sum(b["n"] for b in c["buckets"]) == 6, "every send lands in exactly one bucket"
    assert c["buckets"][0]["n"] >= 1


def test_calibration_buckets_partition_the_full_ledger(monkeypatch):
    monkeypatch.setattr(build_site, "joined", lambda: fake(417, 5))
    c = build_site.calibration_rows()
    assert [b["n"] for b in c["buckets"]] == [41, 63, 104, 209]
    assert c["buckets"][0]["k"] == 5
