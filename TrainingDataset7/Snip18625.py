def test_parametrized_db_type(self):
        with self.assertRaises(DataError):
            Reporter.objects.bulk_create(
                [
                    Reporter(),
                    Reporter(first_name="a" * 31),
                ]
            )