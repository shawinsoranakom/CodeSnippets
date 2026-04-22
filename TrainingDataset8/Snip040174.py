def test_get_module_paths_outputs_abs_paths():
    mock_module = MagicMock()
    mock_module.__file__ = os.path.relpath(DUMMY_MODULE_1_FILE)

    module_paths = local_sources_watcher.get_module_paths(mock_module)
    assert module_paths == {DUMMY_MODULE_1_FILE}