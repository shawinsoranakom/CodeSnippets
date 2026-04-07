def test_create_callable_default(self):
        obj, created = Person.objects.update_or_create(
            first_name="George",
            last_name="Harrison",
            defaults={"birthday": lambda: date(1943, 2, 25)},
        )
        self.assertIs(created, True)
        self.assertEqual(obj.birthday, date(1943, 2, 25))