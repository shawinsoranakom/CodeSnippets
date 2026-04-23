def _get_post(self):
        if not hasattr(self, "_post"):
            self._load_post_and_files()
        return self._post