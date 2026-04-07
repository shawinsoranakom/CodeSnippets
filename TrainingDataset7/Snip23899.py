def test_get_or_create_method_with_create(self):
        created = Person.objects.get_or_create(
            first_name="George",
            last_name="Harrison",
            defaults={"birthday": date(1943, 2, 25)},
        )[1]
        self.assertTrue(created)
        self.assertEqual(Person.objects.count(), 2)