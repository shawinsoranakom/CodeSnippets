def test_serialize_iterators(self):
        self.assertSerializedResultEqual(
            ((x, x * x) for x in range(3)), ("((0, 0), (1, 1), (2, 4))", set())
        )