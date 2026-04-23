def test_version_dev_tuple(self):
        expect = ("1.2.3dev", 1, 2, 3)
        ops = FakePostGISOperations(expect[0])
        actual = ops.postgis_version_tuple()
        self.assertEqual(expect, actual)