def test_repr(self):
        admin_site = CustomAdminSite(name="other")
        self.assertEqual(repr(admin_site), "CustomAdminSite(name='other')")