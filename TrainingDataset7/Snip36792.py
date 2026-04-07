def test_primary_key_is_considered_unique(self):
        m = CustomPKModel()
        self.assertEqual(
            ([(CustomPKModel, ("my_pk_field",))], []), m._get_unique_checks()
        )