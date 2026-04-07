def create_storage(self, params):
        params = params.copy()
        backend = params.pop("BACKEND")
        options = params.pop("OPTIONS", {})
        try:
            storage_cls = import_string(backend)
        except ImportError as e:
            raise InvalidStorageError(f"Could not find backend {backend!r}: {e}") from e
        return storage_cls(**options)