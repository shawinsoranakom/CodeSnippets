def test_include_app_name(self):
        self.assertEqual(include(self.app_urls), (self.app_urls, "inc-app", "inc-app"))