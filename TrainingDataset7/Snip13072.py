def create_connection(self, alias):
        params = self.settings[alias]
        backend = params["BACKEND"]
        try:
            backend_cls = import_string(backend)
        except ImportError as e:
            raise InvalidTaskBackend(f"Could not find backend '{backend}': {e}") from e
        return backend_cls(alias=alias, params=params)