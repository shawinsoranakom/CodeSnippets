def __exit__(self, type, value, traceback):
        if self._added_path:
            try:
                sys.path.remove(self._main_script_path)
            except ValueError:
                # It's already removed.
                pass

        # Returning False causes any exceptions to be re-raised.
        return False