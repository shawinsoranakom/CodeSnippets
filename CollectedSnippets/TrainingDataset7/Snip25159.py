def test_i18n_app_dirs_ignore_django_apps(self):
        mocked_sender = mock.MagicMock()
        with self.settings(INSTALLED_APPS=["django.contrib.admin"]):
            watch_for_translation_changes(mocked_sender)
        mocked_sender.watch_dir.assert_called_once_with(Path("locale"), "**/*.mo")