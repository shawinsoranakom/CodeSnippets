def test_no_root_urlconf_in_settings(self):
        delattr(settings, "ROOT_URLCONF")
        result = check_url_config(None)
        self.assertEqual(result, [])