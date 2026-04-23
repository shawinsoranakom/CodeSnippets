def test_custom_adminsite(self):
        class CustomAdminSite(admin.AdminSite):
            pass

        custom_site = CustomAdminSite()
        custom_site.register(Song, MyAdmin)
        try:
            errors = checks.run_checks()
            expected = ["error!"]
            self.assertEqual(errors, expected)
        finally:
            custom_site.unregister(Song)