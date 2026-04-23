def skip_module_if_py_gte_314():
    """Skip entire module on Python 3.14+ at import time."""
    if sys.version_info >= (3, 14):
        pytest.skip("requires python3.13-", allow_module_level=True)