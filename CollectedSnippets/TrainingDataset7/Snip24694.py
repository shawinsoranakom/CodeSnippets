def test_valid_version_numbers(self):
        versions = [
            ("1.3.0", 1, 3, 0),
            ("2.1.1", 2, 1, 1),
            ("2.2.0dev", 2, 2, 0),
        ]

        for version in versions:
            with self.subTest(version=version):
                ops = FakePostGISOperations(version[0])
                actual = ops.spatial_version
                self.assertEqual(version[1:], actual)