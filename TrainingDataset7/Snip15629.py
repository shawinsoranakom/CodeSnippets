def test_custom_site_registration(self):
        register(Person, site=self.custom_site)(NameAdmin)
        self.assertIsInstance(
            self.custom_site.get_model_admin(Person), admin.ModelAdmin
        )