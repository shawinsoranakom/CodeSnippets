def test_race_condition_exist_ok_true(self):
        path = os.path.join(self.base, "a", "b")

        original_mkdir = os.mkdir
        call_count = [0]

        def mkdir_with_race(p, mode):
            call_count[0] += 1
            if call_count[0] == 1:
                original_mkdir(p, mode)
            else:
                # Simulate other thread creating the directory during the race.
                # The directory needs to exist for `exist_ok=True` to succeed.
                original_mkdir(p, mode)
                raise FileExistsError(f"Directory exists: '{p}'")

        with unittest.mock.patch("os.mkdir", side_effect=mkdir_with_race):
            safe_makedirs(path, mode=0o755, exist_ok=True)

        self.assertIs(os.path.isdir(path), True)