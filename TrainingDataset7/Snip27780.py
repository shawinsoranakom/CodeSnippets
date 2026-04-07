def test_max_length(self):
        dm = DataModel(short_data=self.binary_data * 4)
        with self.assertRaises(ValidationError):
            dm.full_clean()