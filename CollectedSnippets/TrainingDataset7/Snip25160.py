def test_i18n_local_locale(self):
        mocked_sender = mock.MagicMock()
        watch_for_translation_changes(mocked_sender)
        locale_dir = Path(__file__).parent / "locale"
        mocked_sender.watch_dir.assert_any_call(locale_dir, "**/*.mo")