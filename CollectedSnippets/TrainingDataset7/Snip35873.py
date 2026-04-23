def test_include_app_name_namespace(self):
        self.assertEqual(
            include(self.app_urls, "namespace"), (self.app_urls, "inc-app", "namespace")
        )