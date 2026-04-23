def assertSerializedFieldEqual(self, value):
        new_value = self.serialize_round_trip(value)
        self.assertEqual(value.__class__, new_value.__class__)
        self.assertEqual(value.max_length, new_value.max_length)
        self.assertEqual(value.null, new_value.null)
        self.assertEqual(value.unique, new_value.unique)