def test_defaults_exact(self):
        """
        If you have a field named defaults and want to use it as an exact
        lookup, you need to use 'defaults__exact'.
        """
        obj, created = Person.objects.update_or_create(
            first_name="George",
            last_name="Harrison",
            defaults__exact="testing",
            defaults={
                "birthday": date(1943, 2, 25),
                "defaults": "testing",
            },
        )
        self.assertTrue(created)
        self.assertEqual(obj.defaults, "testing")
        obj, created = Person.objects.update_or_create(
            first_name="George",
            last_name="Harrison",
            defaults__exact="testing",
            defaults={
                "birthday": date(1943, 2, 25),
                "defaults": "another testing",
            },
        )
        self.assertFalse(created)
        self.assertEqual(obj.defaults, "another testing")