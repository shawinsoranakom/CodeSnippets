def test_version_loose_tuple(self):
        expect = ("1.2.3b1.dev0", 1, 2, 3)
        ops = FakePostGISOperations(expect[0])
        actual = ops.postgis_version_tuple()
        self.assertEqual(expect, actual)