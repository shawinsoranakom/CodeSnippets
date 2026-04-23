def test_existing_directory_exist_ok_false_raises(self):
        path = os.path.join(self.base, "a")
        os.mkdir(path)

        with self.assertRaises(FileExistsError):
            safe_makedirs(path, mode=0o755, exist_ok=False)