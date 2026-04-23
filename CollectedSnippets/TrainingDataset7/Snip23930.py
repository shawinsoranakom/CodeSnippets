def test_create_defaults_exact(self):
        """
        If you have a field named create_defaults and want to use it as an
        exact lookup, you need to use 'create_defaults__exact'.
        """
        obj, created = Person.objects.update_or_create(
            first_name="George",
            last_name="Harrison",
            create_defaults__exact="testing",
            create_defaults={
                "birthday": date(1943, 2, 25),
                "create_defaults": "testing",
            },
        )
        self.assertIs(created, True)
        self.assertEqual(obj.create_defaults, "testing")
        obj, created = Person.objects.update_or_create(
            first_name="George",
            last_name="Harrison",
            create_defaults__exact="testing",
            create_defaults={
                "birthday": date(1943, 2, 25),
                "create_defaults": "another testing",
            },
        )
        self.assertIs(created, False)
        self.assertEqual(obj.create_defaults, "testing")