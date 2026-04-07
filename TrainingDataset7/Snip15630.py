def test_multiple_registration(self):
        register(Traveler, Place)(NameAdmin)
        self.assertIsInstance(
            self.default_site.get_model_admin(Traveler), admin.ModelAdmin
        )
        self.default_site.unregister(Traveler)
        self.assertIsInstance(
            self.default_site.get_model_admin(Place), admin.ModelAdmin
        )
        self.default_site.unregister(Place)