def clear_expired(cls):
        storage_path = cls._get_storage_path()
        file_prefix = settings.SESSION_COOKIE_NAME

        for session_file in os.listdir(storage_path):
            if not session_file.startswith(file_prefix):
                continue
            session_key = session_file.removeprefix(file_prefix)
            session = cls(session_key)
            # When an expired session is loaded, its file is removed, and a
            # new file is immediately created. Prevent this by disabling
            # the create() method.
            session.create = lambda: None
            session.load()