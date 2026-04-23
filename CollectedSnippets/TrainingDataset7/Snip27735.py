def test_serialize_generic_alias(self):
        self.assertSerializedEqual(dict[str, float])