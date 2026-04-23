def summarize(report_path: str):
    p = Path(report_path)
    if not p.exists():
        raise FileNotFoundError(f"Report file not found: {p.resolve()}")

    data = json.loads(p.read_text())
    tests = data.get("tests", [])

    # Overall counts
    outcomes = Counter(t.get("outcome", "unknown") for t in tests)

    # Filter failures (pytest-json-report uses "failed" and may have "error")
    failed = [t for t in tests if t.get("outcome") in ("failed", "error")]

    # 1) Failures per test file
    failures_per_file = Counter(_file_path(t.get("nodeid", "")) for t in failed)

    # 2) Failures per class (if any; otherwise "NO_CLASS")
    failures_per_class = Counter((_class_name(t.get("nodeid", "")) or "NO_CLASS") for t in failed)

    # 3) Failures per base test name (function), aggregating parametrized cases
    failures_per_testname = Counter(_base_test_name(t.get("nodeid", "")) for t in failed)

    # 4) Failures per test_modeling_xxx (derived from filename)
    failures_per_modeling_key = Counter()
    for t in failed:
        key = _modeling_key(_file_path(t.get("nodeid", "")))
        if key:
            failures_per_modeling_key[key] += 1

    return {
        "outcomes": outcomes,
        "failures_per_file": failures_per_file,
        "failures_per_class": failures_per_class,
        "failures_per_testname": failures_per_testname,
        "failures_per_modeling_key": failures_per_modeling_key,
    }