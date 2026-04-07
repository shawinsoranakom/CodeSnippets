def list(self, ignore_patterns):
        """
        List all files in all app storages.
        """
        for storage in self.storages.values():
            if storage.exists(""):  # check if storage location exists
                for path in utils.get_files(storage, ignore_patterns):
                    yield path, storage