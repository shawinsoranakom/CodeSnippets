def test_existing_parent_preserves_permissions(self):
        a = os.path.join(self.base, "a")
        b = os.path.join(a, "b")

        os.mkdir(a, 0o700)

        safe_makedirs(b, mode=0o755, exist_ok=False)

        self.assertDirMode(a, 0o700)
        self.assertDirMode(b, 0o755)

        c = os.path.join(a, "c")
        safe_makedirs(c, mode=0o750, exist_ok=True)

        self.assertDirMode(a, 0o700)
        self.assertDirMode(c, 0o750)