def test_bare_registration(self):
        self.site.register(Person)
        self.assertIsInstance(self.site.get_model_admin(Person), admin.ModelAdmin)
        self.site.unregister(Person)
        self.assertEqual(self.site._registry, {})