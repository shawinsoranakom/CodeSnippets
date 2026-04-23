def print_test_report(results: Dict[str, TestResult]):
    print("\n=== 🔍 Test Report ===")

    max_name_len = max(len(name) for name in results)

    for name, result in results.items():
        status = "✅" if result.passed else "❌"
        if result.expected_failure:
            status = "⚠️" if result.passed else "✓"  # Expected failure case

        print(f"{status} {name.ljust(max_name_len)} {result.duration:.2f}s")

        if result.error:
            print(f"   REQUEST ERROR: {result.error}")
        if result.validation_error:
            print(f"   VALIDATION ERROR: {result.validation_error}")

        if result.result and not result.passed:
            print(f"   STATUS: {result.result.status}")
            if result.result.stderr:
                print(f"   STDERR: {result.result.stderr[:200]}...")
            if result.result.detail:
                print(f"   DETAIL: {result.result.detail}")

    passed = sum(1 for r in results.values() if ((not r.expected_failure and r.passed) or (r.expected_failure and not r.passed)))
    failed = len(results) - passed

    print("\n=== 📊 Statistics ===")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📌 Total: {len(results)}")