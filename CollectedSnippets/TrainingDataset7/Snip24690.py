def test_get_version(self):
        expect = "1.0.0"
        ops = FakePostGISOperations(expect)
        actual = ops.postgis_lib_version()
        self.assertEqual(expect, actual)