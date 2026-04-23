def get_runner(settings, test_runner_class=None):
    test_runner_class = test_runner_class or settings.TEST_RUNNER
    test_path = test_runner_class.split(".")
    # Allow for relative paths
    if len(test_path) > 1:
        test_module_name = ".".join(test_path[:-1])
    else:
        test_module_name = "."
    test_module = __import__(test_module_name, {}, {}, test_path[-1])
    return getattr(test_module, test_path[-1])