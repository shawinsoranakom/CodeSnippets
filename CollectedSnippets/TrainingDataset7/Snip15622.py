def test_iterable_registration(self):
        self.site.register([Person, Place], search_fields=["name"])
        self.assertIsInstance(self.site.get_model_admin(Person), admin.ModelAdmin)
        self.assertEqual(self.site.get_model_admin(Person).search_fields, ["name"])
        self.assertIsInstance(self.site.get_model_admin(Place), admin.ModelAdmin)
        self.assertEqual(self.site.get_model_admin(Place).search_fields, ["name"])
        self.site.unregister([Person, Place])
        self.assertEqual(self.site._registry, {})