def test_app_translation(self):
        # Original translation.
        self.assertGettext("Date/time", "Datum/Zeit")

        # Different translation.
        with self.modify_settings(INSTALLED_APPS={"append": "i18n.resolution"}):
            # Force refreshing translations.
            activate("de")

            # Doesn't work because it's added later in the list.
            self.assertGettext("Date/time", "Datum/Zeit")

            with self.modify_settings(
                INSTALLED_APPS={"remove": "django.contrib.admin.apps.SimpleAdminConfig"}
            ):
                # Force refreshing translations.
                activate("de")

                # Unless the original is removed from the list.
                self.assertGettext("Date/time", "Datum/Zeit (APP)")