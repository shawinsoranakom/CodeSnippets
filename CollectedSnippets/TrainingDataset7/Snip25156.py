def test_i18n_enabled(self):
        mocked_sender = mock.MagicMock()
        watch_for_translation_changes(mocked_sender)
        self.assertGreater(mocked_sender.watch_dir.call_count, 1)