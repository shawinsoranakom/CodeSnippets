def _init_db(self):
        try:
            self._setup_db()
        except Exception:
            exception("Unable to init cache", sys.exc_info())
            self._db = {}