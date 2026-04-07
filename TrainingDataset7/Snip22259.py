def test_fixture_dirs_with_duplicates(self):
        """
        settings.FIXTURE_DIRS cannot contain duplicates in order to avoid
        repeated fixture loading.
        """
        with self.assertRaisesMessage(
            ImproperlyConfigured, "settings.FIXTURE_DIRS contains duplicates."
        ):
            management.call_command("loaddata", "absolute.json", verbosity=0)