def reduce_by_model(logs, error_filter=None):
    """count each error per model"""

    logs = [(x[0], x[1], get_model(x[2])) for x in logs]
    logs = [x for x in logs if x[2] is not None]
    tests = {x[2] for x in logs}

    r = {}
    for test in tests:
        counter = Counter()
        # count by errors in `test`
        counter.update([x[1] for x in logs if x[2] == test])
        counts = counter.most_common()
        error_counts = {error: count for error, count in counts if (error_filter is None or error not in error_filter)}
        n_errors = sum(error_counts.values())
        if n_errors > 0:
            r[test] = {"count": n_errors, "errors": error_counts}

    r = dict(sorted(r.items(), key=lambda item: item[1]["count"], reverse=True))
    return r