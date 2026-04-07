def mkdir_with_race(p, mode):
            call_count[0] += 1
            if call_count[0] == 1:
                original_mkdir(p, mode)
            else:
                raise FileExistsError(f"Directory exists: '{p}'")