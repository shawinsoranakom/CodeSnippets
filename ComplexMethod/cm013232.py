def check_if_enable(test: unittest.TestCase):
    classname = str(test.__class__).split("'")[1].split(".")[-1]
    sanitized_testname = remove_device_and_dtype_suffixes(test._testMethodName)

    def matches_test(target: str):
        target_test_parts = target.split()
        if len(target_test_parts) < 2:
            # poorly formed target test name
            return False
        target_testname = target_test_parts[0]
        target_classname = target_test_parts[1][1:-1].split(".")[-1]
        # if test method name or its sanitized version exactly matches the disabled
        # test method name AND allow non-parametrized suite names to disable
        # parametrized ones (TestSuite disables TestSuiteCPU)
        return classname.startswith(target_classname) and (target_testname in (test._testMethodName, sanitized_testname))

    if any(matches_test(x) for x in slow_tests_dict):
        getattr(test, test._testMethodName).__dict__['slow_test'] = True
        if not TEST_WITH_SLOW:
            raise unittest.SkipTest("test is slow; run with PYTORCH_TEST_WITH_SLOW to enable test")

    if not IS_SANDCASTLE:
        should_skip = False
        skip_msg = ""

        for disabled_test, (issue_url, platforms) in disabled_tests_dict.items():
            if matches_test(disabled_test):
                platform_to_conditional: dict = {
                    "mac": IS_MACOS,
                    "macos": IS_MACOS,
                    "win": IS_WINDOWS,
                    "windows": IS_WINDOWS,
                    "linux": IS_LINUX,
                    "rocm": TEST_WITH_ROCM,
                    "xpu": TEST_XPU,
                    "asan": TEST_WITH_ASAN,
                    "dynamo": TEST_WITH_TORCHDYNAMO,
                    "dynamo_wrapped": TEST_WITH_TORCHDYNAMO,
                    "inductor": TEST_WITH_TORCHINDUCTOR,
                    "slow": TEST_WITH_SLOW,
                }

                invalid_platforms = list(filter(lambda p: p not in platform_to_conditional, platforms))
                if len(invalid_platforms) > 0:
                    invalid_plats_str = ", ".join(invalid_platforms)
                    valid_plats = ", ".join(platform_to_conditional.keys())

                    print(f"Test {disabled_test} is disabled for some unrecognized ",
                          f"platforms: [{invalid_plats_str}]. Please edit issue {issue_url} to fix the platforms ",
                          'assigned to this flaky test, changing "Platforms: ..." to a comma separated ',
                          f"subset of the following (or leave it blank to match all platforms): {valid_plats}")

                    # Sanitize the platforms list so that we continue to disable the test for any valid platforms given
                    platforms = list(filter(lambda p: p in platform_to_conditional, platforms))

                if platforms == [] or any(platform_to_conditional[platform] for platform in platforms):
                    should_skip = True
                    skip_msg = f"Test is disabled because an issue exists disabling it: {issue_url}" \
                        f" for {'all' if platforms == [] else ''}platform(s) {', '.join(platforms)}. " \
                        "If you're seeing this on your local machine and would like to enable this test, " \
                        "please make sure CI is not set and you are not using the flag --import-disabled-tests."
                    break

        if should_skip and not RERUN_DISABLED_TESTS:
            # Skip the disabled test when not running under --rerun-disabled-tests verification mode
            raise unittest.SkipTest(skip_msg)

        if not should_skip and RERUN_DISABLED_TESTS:
            # Probably test has disable issue but not for this platform
            skip_msg = "Test is enabled but --rerun-disabled-tests verification mode is set, so only" \
                " disabled tests are run"
            raise unittest.SkipTest(skip_msg)

    if TEST_SKIP_FAST:
        if hasattr(test, test._testMethodName) and not getattr(test, test._testMethodName).__dict__.get('slow_test', False):
            raise unittest.SkipTest("test is fast; we disabled it with PYTORCH_TEST_SKIP_FAST")