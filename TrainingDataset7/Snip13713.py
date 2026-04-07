def _run_subsuite(args):
    """
    Run a suite of tests with a RemoteTestRunner and return a RemoteTestResult.

    This helper lives at module-level and its arguments are wrapped in a tuple
    because of the multiprocessing module's requirements.
    """
    runner_class, subsuite_index, subsuite, failfast, buffer = args
    runner = runner_class(failfast=failfast, buffer=buffer)
    result = runner.run(subsuite)
    return subsuite_index, result.events