def _get_storage_path(cls):
        try:
            return cls._storage_path
        except AttributeError:
            storage_path = (
                getattr(settings, "SESSION_FILE_PATH", None) or tempfile.gettempdir()
            )
            # Make sure the storage path is valid.
            if not os.path.isdir(storage_path):
                raise ImproperlyConfigured(
                    "The session storage path %r doesn't exist. Please set your"
                    " SESSION_FILE_PATH setting to an existing directory in which"
                    " Django can store session data." % storage_path
                )

            cls._storage_path = storage_path
            return storage_path