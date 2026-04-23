def test_use_custom_admin_site(self):
        self.assertEqual(admin.site.__class__.__name__, "CustomAdminSite")