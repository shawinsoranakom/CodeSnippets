def test_installs_pages_watcher_on_init(self, patched_register_callback):
        session = _create_test_session()
        patched_register_callback.assert_called_once_with(session._on_pages_changed)