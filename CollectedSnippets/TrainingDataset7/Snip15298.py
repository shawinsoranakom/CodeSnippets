def test_use_default_admin_site(self):
        self.assertEqual(admin.site.__class__.__name__, "AdminSite")