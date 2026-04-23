def run_test_plan(
    test_plan: str,
    test_target: str,
    tests_map: dict[str, Any],
    shard_id: int = 0,
    num_shards: int = 0,
):
    """
    a method to run list of tests based on the test plan.
    """
    logger.info("run %s tests.....", test_target)
    if test_plan not in tests_map:
        raise RuntimeError(
            f"test {test_plan} not found, please add it to test plan pool"
        )
    tests = tests_map[test_plan]
    pkgs = tests.get("package_install", [])
    title = tests.get("title", "unknown test")

    is_parallel = check_parallelism(tests, title, shard_id, num_shards)
    if is_parallel:
        title = title.replace("%N", f"{shard_id}/{num_shards}")

    disabled_tests = _load_disabled_vllm_tests()
    disabled_flags = _build_disabled_test_flags(disabled_tests, test_plan)
    if disabled_flags:
        logger.info("Disabled test flags for %s: %s", test_plan, disabled_flags)

    logger.info("Running tests: %s", title)
    if pkgs:
        logger.info("Installing packages: %s", pkgs)
        pip_install_packages(packages=pkgs, prefer_uv=True)
    with (
        working_directory(tests.get("working_directory", "tests")),
        temp_environ(tests.get("env_vars", {})),
    ):
        failures = []
        for step in tests["steps"]:
            logger.info("Running step: %s", step)
            if is_parallel:
                step = replace_buildkite_placeholders(step, shard_id, num_shards)
                logger.info("Running parallel step: %s", step)
            if "pytest" in step:
                # Inject disabled test flags before rerun flags
                if disabled_flags:
                    step = step.replace("pytest", f"pytest {disabled_flags}", 1)
                # Support retry with delay for all pytest commands, pytest-rerunfailures
                # is already a dependency of vLLM. This is needed as a stop gap to reduce
                # the number of requests to HF until #172300 can be landed to enable
                # HF offline mode.
                # Use a low retry count and a high delay value to lower the risk of
                # having a retry storm and make thing worse
                rerun_count = os.getenv(
                    "VLLM_RERUN_FAILURES_COUNT", VLLM_DEFAULT_RERUN_FAILURES_COUNT
                )
                rerun_delay = os.getenv(
                    "VLLM_RERUN_FAILURES_DELAY", VLLM_DEFAULT_RERUN_FAILURES_DELAY
                )
                if rerun_delay:
                    step = step.replace(
                        "pytest",
                        f"pytest --reruns {rerun_count} --reruns-delay {rerun_delay}",
                        1,
                    )
                else:
                    step = step.replace(
                        "pytest",
                        f"pytest --reruns {rerun_count}",
                        1,
                    )

            code = run_command(cmd=step, check=False, use_shell=True)
            if code != 0:
                failures.append(step)
            logger.info("Finish running step: %s", step)
        if failures:
            logger.error("Failed tests: %s", failures)
            raise RuntimeError(f"{len(failures)} pytest runs failed: {failures}")
        logger.info("Done. All tests passed")