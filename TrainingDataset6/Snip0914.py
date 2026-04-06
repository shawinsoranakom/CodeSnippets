def pytest_addoption(parser):
    """Adds `--enable-functional` argument."""
    group = parser.getgroup("thefuck")
    group.addoption('--enable-functional', action="store_true", default=False,
                    help="Enable functional tests")