def _delete(self, fname):
        if not fname.startswith(self._dir) or not os.path.exists(fname):
            return False
        try:
            os.remove(fname)
        except FileNotFoundError:
            # The file may have been removed by another process.
            return False
        return True