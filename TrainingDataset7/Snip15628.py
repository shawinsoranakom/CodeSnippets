def test_basic_registration(self):
        register(Person)(NameAdmin)
        self.assertIsInstance(
            self.default_site.get_model_admin(Person), admin.ModelAdmin
        )
        self.default_site.unregister(Person)