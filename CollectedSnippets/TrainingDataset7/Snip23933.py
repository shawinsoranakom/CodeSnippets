def test_update_callable_default(self):
        Person.objects.update_or_create(
            first_name="George",
            last_name="Harrison",
            birthday=date(1942, 2, 25),
        )
        obj, created = Person.objects.update_or_create(
            first_name="George",
            defaults={"last_name": lambda: "NotHarrison"},
        )
        self.assertIs(created, False)
        self.assertEqual(obj.last_name, "NotHarrison")