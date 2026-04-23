def mkdir_changing_umask(p, mode):
            # Simulate a concurrent thread changing the process umask.
            os.umask(0o077)
            original_mkdir(p, mode)