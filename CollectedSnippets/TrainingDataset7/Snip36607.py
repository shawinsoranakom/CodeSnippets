def test_file_in_intermediate_path_raises(self):
        file_path = os.path.join(self.base, "a")
        with open(file_path, "w") as f:
            f.write("x")

        path = os.path.join(file_path, "b")

        expected = FileNotFoundError if sys.platform == "win32" else NotADirectoryError

        with self.assertRaises(expected):
            safe_makedirs(path, mode=0o755, exist_ok=False)

        with self.assertRaises(expected):
            safe_makedirs(path, mode=0o755, exist_ok=True)