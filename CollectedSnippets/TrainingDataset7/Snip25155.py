def test_i18n_disabled(self):
        mocked_sender = mock.MagicMock()
        watch_for_translation_changes(mocked_sender)
        mocked_sender.watch_dir.assert_not_called()