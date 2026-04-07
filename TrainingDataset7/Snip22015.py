def read_and_close(f):
        with f:
            return f.read().decode()