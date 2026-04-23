def test_new_object_create(self):
        test_co = Company.objects.create(
            name=Lower(Value("UPPER")), num_employees=32, num_chairs=1, ceo=self.max
        )
        test_co.refresh_from_db()
        self.assertEqual(test_co.name, "upper")