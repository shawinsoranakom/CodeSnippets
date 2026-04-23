def test_registration_with_model_admin(self):
        self.site.register(Person, NameAdmin)
        self.assertIsInstance(self.site.get_model_admin(Person), NameAdmin)
        self.site.unregister(Person)
        self.assertEqual(self.site._registry, {})