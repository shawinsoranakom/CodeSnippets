def test_i18n_app_dirs(self):
        mocked_sender = mock.MagicMock()
        with self.settings(INSTALLED_APPS=["i18n.sampleproject"]):
            watch_for_translation_changes(mocked_sender)
        project_dir = Path(__file__).parent / "sampleproject" / "locale"
        mocked_sender.watch_dir.assert_any_call(project_dir, "**/*.mo")