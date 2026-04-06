def _setup_db(self):
        cache_dir = self._get_cache_dir()
        cache_path = Path(cache_dir).joinpath('thefuck').as_posix()

        try:
            self._db = shelve.open(cache_path)
        except shelve_open_error + (ImportError,):
            # Caused when switching between Python versions
            warn("Removing possibly out-dated cache")
            os.remove(cache_path)
            self._db = shelve.open(cache_path)

        atexit.register(self._db.close)