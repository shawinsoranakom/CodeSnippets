def test_basic(self):
        """
        #15346, #15573 - create_default_site() creates an example site only if
        none exist.
        """
        with captured_stdout() as stdout:
            create_default_site(self.app_config)
        self.assertEqual(Site.objects.count(), 1)
        self.assertIn("Creating example.com", stdout.getvalue())

        with captured_stdout() as stdout:
            create_default_site(self.app_config)
        self.assertEqual(Site.objects.count(), 1)
        self.assertEqual("", stdout.getvalue())