def test_normalize_path_patterns_truncates_wildcard_base(self):
        expected = [os.path.normcase(p) for p in ["foo/bar", "bar/*/"]]
        self.assertEqual(normalize_path_patterns(["foo/bar/*", "bar/*/"]), expected)