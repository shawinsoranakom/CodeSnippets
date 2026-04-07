def upload_handlers(self):
        if not self._upload_handlers:
            # If there are no upload handlers defined, initialize them from
            # settings.
            self._initialize_handlers()
        return self._upload_handlers