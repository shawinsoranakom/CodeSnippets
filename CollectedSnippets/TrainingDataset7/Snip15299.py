def test_repr(self):
        self.assertEqual(str(admin.site), "AdminSite(name='admin')")
        self.assertEqual(repr(admin.site), "AdminSite(name='admin')")