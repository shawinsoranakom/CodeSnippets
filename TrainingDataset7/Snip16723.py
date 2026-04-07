def test_check(self):
        "The view_on_site value is either a boolean or a callable"
        try:
            admin = CityAdmin(City, AdminSite())
            CityAdmin.view_on_site = True
            self.assertEqual(admin.check(), [])
            CityAdmin.view_on_site = False
            self.assertEqual(admin.check(), [])
            CityAdmin.view_on_site = lambda obj: obj.get_absolute_url()
            self.assertEqual(admin.check(), [])
            CityAdmin.view_on_site = []
            self.assertEqual(
                admin.check(),
                [
                    Error(
                        "The value of 'view_on_site' must be a callable or a boolean "
                        "value.",
                        obj=CityAdmin,
                        id="admin.E025",
                    ),
                ],
            )
        finally:
            # Restore the original values for the benefit of other tests.
            CityAdmin.view_on_site = True