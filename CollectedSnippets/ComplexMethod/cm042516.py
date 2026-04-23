def pytest_runtest_setup(item):
    # Skip tests based on reactor markers
    reactor = item.config.getoption("--reactor")

    if item.get_closest_marker("requires_reactor") and reactor == "none":
        pytest.skip('This test is only run when the --reactor value is not "none"')

    if item.get_closest_marker("only_asyncio") and reactor not in {"asyncio", "none"}:
        pytest.skip(
            'This test is only run when the --reactor value is "asyncio" (default) or "none"'
        )

    if item.get_closest_marker("only_not_asyncio") and reactor in {"asyncio", "none"}:
        pytest.skip(
            'This test is only run when the --reactor value is not "asyncio" (default) or "none"'
        )

    # Skip tests requiring optional dependencies
    optional_deps = [
        "uvloop",
        "botocore",
        "boto3",
        "mitmproxy",
    ]

    for module in optional_deps:
        if item.get_closest_marker(f"requires_{module}"):
            try:
                importlib.import_module(module)
            except ImportError:
                pytest.skip(f"{module} is not installed")