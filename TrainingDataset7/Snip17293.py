def test_duplicate_names(self):
        with self.assertRaisesMessage(
            ImproperlyConfigured, "Application names aren't unique"
        ):
            with self.settings(
                INSTALLED_APPS=["apps.apps.RelabeledAppsConfig", "apps"]
            ):
                pass