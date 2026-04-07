def test_create_twice(self):
        p, created = Person.objects.update_or_create(
            first_name="John",
            last_name="Lennon",
            create_defaults={"birthday": date(1940, 10, 10)},
            defaults={"birthday": date(1950, 2, 2)},
        )
        self.assertIs(created, True)
        self.assertEqual(p.birthday, date(1940, 10, 10))
        # If we execute the exact same statement, it won't create a Person, but
        # will update the birthday.
        p, created = Person.objects.update_or_create(
            first_name="John",
            last_name="Lennon",
            create_defaults={"birthday": date(1940, 10, 10)},
            defaults={"birthday": date(1950, 2, 2)},
        )
        self.assertIs(created, False)
        self.assertEqual(p.birthday, date(1950, 2, 2))