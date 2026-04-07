def test_fixture_dirs_with_default_fixture_path(self):
        """
        settings.FIXTURE_DIRS cannot contain a default fixtures directory
        for application (app/fixtures) in order to avoid repeated fixture
        loading.
        """
        msg = (
            "'%s' is a default fixture directory for the '%s' app "
            "and cannot be listed in settings.FIXTURE_DIRS."
            % (os.path.join(_cur_dir, "fixtures"), "fixtures_regress")
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            management.call_command("loaddata", "absolute.json", verbosity=0)