def teardown_run_tests(state):
    teardown_collect_tests(state)
    del os.environ["RUNNING_DJANGOS_TEST_SUITE"]