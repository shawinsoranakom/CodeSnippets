def test_foreign_key_validation(self):
        "ForeignKey.validate() uses the correct database"
        mickey = Person.objects.using("other").create(name="Mickey")
        pluto = Pet.objects.using("other").create(name="Pluto", owner=mickey)
        self.assertIsNone(pluto.full_clean())