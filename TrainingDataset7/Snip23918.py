def test_create(self):
        p, created = Person.objects.update_or_create(
            first_name="John",
            last_name="Lennon",
            defaults={"birthday": date(1940, 10, 10)},
        )
        self.assertTrue(created)
        self.assertEqual(p.first_name, "John")
        self.assertEqual(p.last_name, "Lennon")
        self.assertEqual(p.birthday, date(1940, 10, 10))