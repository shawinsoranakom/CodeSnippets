def _initialize_handlers(self):
        self._upload_handlers = [
            uploadhandler.load_handler(handler, self)
            for handler in settings.FILE_UPLOAD_HANDLERS
        ]