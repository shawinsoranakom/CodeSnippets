def __getitem__(self, alias):
        try:
            return self._storages[alias]
        except KeyError:
            try:
                params = self.backends[alias]
            except KeyError:
                raise InvalidStorageError(
                    f"Could not find config for '{alias}' in settings.STORAGES."
                )
            storage = self.create_storage(params)
            self._storages[alias] = storage
            return storage