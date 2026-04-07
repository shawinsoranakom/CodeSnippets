def test_existing_directory_exist_ok(self):
        path = os.path.join(self.base, "a")
        os.mkdir(path, 0o700)

        safe_makedirs(path, mode=0o755, exist_ok=True)

        self.assertDirMode(path, 0o700)