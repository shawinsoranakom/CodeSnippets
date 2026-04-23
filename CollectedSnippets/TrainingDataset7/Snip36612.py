def test_race_condition_exist_ok_false(self):
        path = os.path.join(self.base, "a", "b")

        original_mkdir = os.mkdir
        call_count = [0]

        # `safe_makedirs()` calls `os.mkdir()` for each level in the path.
        # For path "a/b", mkdir is called twice: once for "a", once for "b".
        def mkdir_with_race(p, mode):
            call_count[0] += 1
            if call_count[0] == 1:
                original_mkdir(p, mode)
            else:
                raise FileExistsError(f"Directory exists: '{p}'")

        with unittest.mock.patch("os.mkdir", side_effect=mkdir_with_race):
            with self.assertRaises(FileExistsError):
                safe_makedirs(path, mode=0o755, exist_ok=False)