def test_new_object_save(self):
        # We should be able to use Funcs when inserting new data
        test_co = Company(
            name=Lower(Value("UPPER")), num_employees=32, num_chairs=1, ceo=self.max
        )
        test_co.save()
        test_co.refresh_from_db()
        self.assertEqual(test_co.name, "upper")