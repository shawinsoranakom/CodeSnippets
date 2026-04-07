def test_get_or_create_redundant_instance(self):
        """
        If we execute the exact same statement twice, the second time,
        it won't create a Person.
        """
        Person.objects.get_or_create(
            first_name="George",
            last_name="Harrison",
            defaults={"birthday": date(1943, 2, 25)},
        )
        created = Person.objects.get_or_create(
            first_name="George",
            last_name="Harrison",
            defaults={"birthday": date(1943, 2, 25)},
        )[1]

        self.assertFalse(created)
        self.assertEqual(Person.objects.count(), 2)