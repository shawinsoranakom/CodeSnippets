def test_permissions_unaffected_by_process_umask(self):
        path = os.path.join(self.base, "a", "b", "c")
        # `umask()` returns the current mask, so it'll be restored on cleanup.
        self.addCleanup(os.umask, os.umask(0o077))

        safe_makedirs(path, mode=0o755)

        self.assertDirMode(os.path.join(self.base, "a"), 0o755)
        self.assertDirMode(os.path.join(self.base, "a", "b"), 0o755)
        self.assertDirMode(path, 0o755)