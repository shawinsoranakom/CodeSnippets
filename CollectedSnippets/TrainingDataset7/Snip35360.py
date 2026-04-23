def test_override_staticfiles_finders(self):
        """
        Overriding the STATICFILES_FINDERS setting should be reflected in
        the return value of django.contrib.staticfiles.finders.get_finders.
        """
        current = get_finders()
        self.assertGreater(len(list(current)), 1)
        finders = ["django.contrib.staticfiles.finders.FileSystemFinder"]
        with self.settings(STATICFILES_FINDERS=finders):
            self.assertEqual(len(list(get_finders())), len(finders))