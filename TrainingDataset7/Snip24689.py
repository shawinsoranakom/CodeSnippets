def test_invalid_has_func_function(self):
        msg = (
            'DatabaseFeatures.has_Invalid_function isn\'t valid. Is "Invalid" '
            "missing from BaseSpatialOperations.unsupported_functions?"
        )
        with self.assertRaisesMessage(ValueError, msg):
            connection.features.has_Invalid_function