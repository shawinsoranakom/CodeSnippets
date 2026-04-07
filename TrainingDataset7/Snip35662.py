def test_update_fields_basic(self):
        s = Person.objects.create(name="Sara", gender="F")
        self.assertEqual(s.gender, "F")

        s.gender = "M"
        s.name = "Ian"
        s.save(update_fields=["name"])

        s = Person.objects.get(pk=s.pk)
        self.assertEqual(s.gender, "F")
        self.assertEqual(s.name, "Ian")