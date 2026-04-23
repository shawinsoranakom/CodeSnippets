def must_serial(file: str | ShardedTest) -> bool:
    if isinstance(file, ShardedTest):
        file = file.name
    return (
        os.getenv("PYTORCH_TEST_RUN_EVERYTHING_IN_SERIAL", "0") == "1"
        or DISTRIBUTED_TEST_PREFIX in os.getenv("TEST_CONFIG", "")
        or DISTRIBUTED_TEST_PREFIX in file
        or file in CUSTOM_HANDLERS
        or file in RUN_PARALLEL_BLOCKLIST
        or file in CI_SERIAL_LIST
        or file in JIT_EXECUTOR_TESTS
        or file in ONNX_SERIAL_LIST
        or NUM_PROCS == 1
    )