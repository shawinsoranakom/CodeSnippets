def test_creates_directory_hierarchy_with_permissions(self):
        path = os.path.join(self.base, "a", "b", "c")
        safe_makedirs(path, mode=0o755)

        self.assertDirMode(os.path.join(self.base, "a"), 0o755)
        self.assertDirMode(os.path.join(self.base, "a", "b"), 0o755)
        self.assertDirMode(path, 0o755)