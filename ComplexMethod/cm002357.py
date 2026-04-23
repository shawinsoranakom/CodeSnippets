def handle_test_results(test_results):
    expressions = test_results.split(" ")

    failed = 0
    success = 0
    errors = 0
    skipped = 0

    # When the output is short enough, the output is surrounded by = signs: "== OUTPUT =="
    # When it is too long, those signs are not present.
    # It could be `'71.60s', '(0:01:11)', '====\n'` or `'in', '35.01s', '================\n'`.
    # Let always select the one with `s`.
    time_spent = expressions[-1]
    if "=" in time_spent:
        time_spent = expressions[-2]
    if "(" in time_spent:
        time_spent = expressions[-3]

    for i, expression in enumerate(expressions):
        if "failed" in expression:
            failed += int(expressions[i - 1])
        if "errors" in expression:
            errors += int(expressions[i - 1])
        if "passed" in expression:
            success += int(expressions[i - 1])
        if "skipped" in expression:
            skipped += int(expressions[i - 1])

    return failed, errors, success, skipped, time_spent