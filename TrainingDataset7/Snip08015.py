def __init__(self, session_key=None):
        self.storage_path = self._get_storage_path()
        self.file_prefix = settings.SESSION_COOKIE_NAME
        super().__init__(session_key)