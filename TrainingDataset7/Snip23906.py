def test_callable_defaults(self):
        """
        Callables in `defaults` are evaluated if the instance is created.
        """
        obj, created = Person.objects.get_or_create(
            first_name="George",
            defaults={"last_name": "Harrison", "birthday": lambda: date(1943, 2, 25)},
        )
        self.assertTrue(created)
        self.assertEqual(date(1943, 2, 25), obj.birthday)