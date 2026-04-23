def test_get_or_create_method_with_get(self):
        created = Person.objects.get_or_create(
            first_name="John",
            last_name="Lennon",
            defaults={"birthday": date(1940, 10, 9)},
        )[1]
        self.assertFalse(created)
        self.assertEqual(Person.objects.count(), 1)