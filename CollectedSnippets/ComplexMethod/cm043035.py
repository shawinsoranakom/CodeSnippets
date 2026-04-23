def check(name, result, expected_blocked, expected_substr=None):
    global PASS, FAIL
    blocked, reason = result
    ok = blocked == expected_blocked
    if expected_substr and blocked:
        ok = ok and expected_substr.lower() in reason.lower()
    status = "PASS" if ok else "FAIL"
    if not ok:
        FAIL += 1
        print(f"  {status}: {name}")
        print(f"         got blocked={blocked}, reason={reason!r}")
        print(f"         expected blocked={expected_blocked}" +
              (f", substr={expected_substr!r}" if expected_substr else ""))
    else:
        PASS += 1
        if blocked:
            print(f"  {status}: {name} -> {reason}")
        else:
            print(f"  {status}: {name} -> not blocked")