def test_path_is_normalized(self):
        path = os.path.join(self.base, "a", "b", "..", "c")
        safe_makedirs(path, mode=0o755)

        self.assertDirMode(os.path.normpath(path), 0o755)
        self.assertIs(os.path.isdir(os.path.join(self.base, "a", "c")), True)