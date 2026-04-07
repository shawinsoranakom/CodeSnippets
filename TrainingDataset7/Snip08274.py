def _is_expired(self, f):
        """
        Take an open cache file `f` and delete it if it's expired.
        """
        try:
            exp = pickle.load(f)
        except EOFError:
            exp = 0  # An empty file is considered expired.
        if exp is not None and exp < time.time():
            f.close()  # On Windows a file has to be closed before deleting
            self._delete(f.name)
            return True
        return False