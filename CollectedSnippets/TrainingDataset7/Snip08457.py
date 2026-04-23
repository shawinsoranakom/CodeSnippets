def lock(f, flags):
            try:
                fcntl.flock(_fd(f), flags)
                return True
            except BlockingIOError:
                return False