def test_existing_file_at_target_raises(self):
        path = os.path.join(self.base, "a")
        with open(path, "w") as f:
            f.write("x")

        with self.assertRaises(FileExistsError):
            safe_makedirs(path, mode=0o755, exist_ok=False)

        with self.assertRaises(FileExistsError):
            safe_makedirs(path, mode=0o755, exist_ok=True)