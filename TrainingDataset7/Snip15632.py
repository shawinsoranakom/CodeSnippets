def test_custom_site_not_an_admin_site(self):
        with self.assertRaisesMessage(ValueError, "site must subclass AdminSite"):
            register(Person, site=Traveler)(NameAdmin)