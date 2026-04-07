def test_releases(self):
        tuples_to_strings = (
            ((1, 4, 0, "alpha", 1), "1.4a1"),
            ((1, 4, 0, "beta", 1), "1.4b1"),
            ((1, 4, 0, "rc", 1), "1.4rc1"),
            ((1, 4, 0, "final", 0), "1.4"),
            ((1, 4, 1, "rc", 2), "1.4.1rc2"),
            ((1, 4, 1, "final", 0), "1.4.1"),
        )
        for ver_tuple, ver_string in tuples_to_strings:
            self.assertEqual(get_version(ver_tuple), ver_string)