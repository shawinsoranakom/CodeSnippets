def mkdir_with_race(p, mode):
            call_count[0] += 1
            if call_count[0] == 1:
                original_mkdir(p, mode)
            else:
                # Simulate other thread creating the directory during the race.
                # The directory needs to exist for `exist_ok=True` to succeed.
                original_mkdir(p, mode)
                raise FileExistsError(f"Directory exists: '{p}'")