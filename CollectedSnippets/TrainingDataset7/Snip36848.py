def test_development(self):
        get_git_changeset.cache_clear()
        ver_tuple = (1, 4, 0, "alpha", 0)
        # This will return a different result when it's run within or outside
        # of a git clone: 1.4.devYYYYMMDDHHMMSS or 1.4.
        ver_string = get_version(ver_tuple)
        self.assertRegex(ver_string, r"1\.4(\.dev[0-9]+)?")