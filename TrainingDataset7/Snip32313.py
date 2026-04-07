def test_valid_site_id(self):
        for site_id in [1, None]:
            with self.subTest(site_id=site_id), self.settings(SITE_ID=site_id):
                self.assertEqual(check_site_id(None), [])