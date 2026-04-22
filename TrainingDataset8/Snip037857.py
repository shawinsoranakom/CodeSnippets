def __init__(self):
        """Initialize class."""
        if Credentials._singleton is not None:
            raise RuntimeError(
                "Credentials already initialized. Use .get_current() instead"
            )

        self.activation = None
        self._conf_file = _get_credential_file_path()

        Credentials._singleton = self