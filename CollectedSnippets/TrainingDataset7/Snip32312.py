def test_check_site_id(self):
        self.assertEqual(
            check_site_id(None),
            [
                checks.Error(
                    msg="The SITE_ID setting must be an integer",
                    id="sites.E101",
                ),
            ],
        )