def _test_error_exc_info():
    try:
        raise ValueError("woops")
    except ValueError:
        return sys.exc_info()