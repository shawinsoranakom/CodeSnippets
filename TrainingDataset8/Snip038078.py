def __enter__(self):
        if self._main_script_path not in sys.path:
            sys.path.insert(0, self._main_script_path)
            self._added_path = True