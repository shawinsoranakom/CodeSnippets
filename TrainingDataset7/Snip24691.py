def test_version_classic_tuple(self):
        expect = ("1.2.3", 1, 2, 3)
        ops = FakePostGISOperations(expect[0])
        actual = ops.postgis_version_tuple()
        self.assertEqual(expect, actual)