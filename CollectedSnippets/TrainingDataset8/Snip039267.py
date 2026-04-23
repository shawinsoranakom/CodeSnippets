def test_deregisters_pages_watcher_on_shutdown(self, patched_on_pages_changed):
        session = _create_test_session()
        session.shutdown()

        patched_on_pages_changed.disconnect.assert_called_once_with(
            session._on_pages_changed
        )