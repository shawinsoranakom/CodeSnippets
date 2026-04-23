def find_in_app(self, app, path):
        """
        Find a requested static file in an app's static locations.
        """
        storage = self.storages.get(app)
        # Only try to find a file if the source dir actually exists.
        if storage and storage.exists(path):
            matched_path = storage.path(path)
            if matched_path:
                return matched_path