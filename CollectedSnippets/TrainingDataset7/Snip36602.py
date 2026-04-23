def assertDirMode(self, path, expected):
        self.assertIs(os.path.isdir(path), True)
        if sys.platform == "win32":
            # Windows partially supports chmod: dirs always end up with 0o777.
            expected = 0o777

        # These tests assume a typical process umask (0o022 or similar): they
        # create directories with modes like 0o755 and 0o700, which don't have
        # group/world write bits, so a typical umask doesn't change the final
        # permissions. On unexpected failures, check whether umask has changed.
        self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), expected)