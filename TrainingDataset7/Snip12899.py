def upload_handlers(self, upload_handlers):
        if hasattr(self, "_files"):
            raise AttributeError(
                "You cannot set the upload handlers after the upload has been "
                "processed."
            )
        self._upload_handlers = upload_handlers