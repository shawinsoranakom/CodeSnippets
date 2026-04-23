def test_serialize_set(self):
        self.assertSerializedEqual(set())
        self.assertSerializedResultEqual(set(), ("set()", set()))
        self.assertSerializedEqual({"a"})
        self.assertSerializedResultEqual({"a"}, ("{'a'}", set()))
        self.assertSerializedEqual({"c", "b", "a"})
        self.assertSerializedResultEqual({"c", "b", "a"}, ("{'a', 'b', 'c'}", set()))