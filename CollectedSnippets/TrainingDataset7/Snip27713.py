def test_serialize_frozensets(self):
        self.assertSerializedEqual(frozenset())
        self.assertSerializedEqual(frozenset("let it go"))
        self.assertSerializedResultEqual(
            frozenset("cba"), ("frozenset(['a', 'b', 'c'])", set())
        )