def test_registration_with_star_star_options(self):
        self.site.register(Person, search_fields=["name"])
        self.assertEqual(self.site.get_model_admin(Person).search_fields, ["name"])