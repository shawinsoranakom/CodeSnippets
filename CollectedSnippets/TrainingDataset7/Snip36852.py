def test_get_version_invalid_version(self):
        tests = [
            # Invalid length.
            (3, 2, 0, "alpha", 1, "20210315111111"),
            # Invalid development status.
            (3, 2, 0, "gamma", 1, "20210315111111"),
        ]
        for version in tests:
            with self.subTest(version=version), self.assertRaises(AssertionError):
                get_complete_version(version)