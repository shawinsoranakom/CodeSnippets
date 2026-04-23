def _get_files(self):
        if not hasattr(self, "_files"):
            self._load_post_and_files()
        return self._files