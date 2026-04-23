def assertSerializedEqual(self, value):
        self.assertEqual(self.serialize_round_trip(value), value)