def test_select_for_update_with_get(self):
        with transaction.atomic():
            person = Person.objects.select_for_update().get(name="Reinhardt")
        self.assertEqual(person.name, "Reinhardt")