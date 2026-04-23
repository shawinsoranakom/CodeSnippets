def unlock(f):
            fcntl.flock(_fd(f), fcntl.LOCK_UN)
            return True