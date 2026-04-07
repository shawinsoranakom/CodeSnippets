def test_permissions_correct_despite_concurrent_umask_change(self):
        path = os.path.join(self.base, "a", "b", "c")
        original_mkdir = os.mkdir
        # `umask()` returns the current mask, so it'll be restored on cleanup.
        self.addCleanup(os.umask, os.umask(0o000))

        def mkdir_changing_umask(p, mode):
            # Simulate a concurrent thread changing the process umask.
            os.umask(0o077)
            original_mkdir(p, mode)

        with unittest.mock.patch("os.mkdir", side_effect=mkdir_changing_umask):
            safe_makedirs(path, mode=0o755)

        self.assertDirMode(os.path.join(self.base, "a"), 0o755)
        self.assertDirMode(os.path.join(self.base, "a", "b"), 0o755)
        self.assertDirMode(path, 0o755)