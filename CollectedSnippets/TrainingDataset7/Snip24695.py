def test_no_version_number(self):
        ops = FakePostGISOperations()
        with self.assertRaises(ImproperlyConfigured):
            ops.spatial_version