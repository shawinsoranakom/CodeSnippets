def list(self, ignore_patterns):
        """
        List all files in all locations.
        """
        for prefix, root in self.locations:
            # Skip nonexistent directories.
            if os.path.isdir(root):
                storage = self.storages[root]
                for path in utils.get_files(storage, ignore_patterns):
                    yield path, storage