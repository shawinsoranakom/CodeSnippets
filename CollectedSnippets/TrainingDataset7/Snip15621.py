def test_star_star_overrides(self):
        self.site.register(
            Person, NameAdmin, search_fields=["name"], list_display=["__str__"]
        )
        person_admin = self.site.get_model_admin(Person)
        self.assertEqual(person_admin.search_fields, ["name"])
        self.assertEqual(person_admin.list_display, ["__str__"])
        self.assertIs(person_admin.save_on_top, True)