def pytest_collection_modifyitems(config, items: list[pytest.Item]) -> None:
    if sys.platform != "win32":
        return

    for item in items:
        item_path = Path(item.fspath).resolve()
        if item_path.is_relative_to(THIS_DIR):
            item.add_marker(skip_on_windows)