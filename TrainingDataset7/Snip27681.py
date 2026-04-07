def test_serialize_constants(self):
        self.assertSerializedEqual(None)
        self.assertSerializedEqual(True)
        self.assertSerializedEqual(False)