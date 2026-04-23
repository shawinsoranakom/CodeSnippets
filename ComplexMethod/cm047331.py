def remove(self, paths_to_remove, bundle):
        """Removes the given paths from the current list."""
        paths = {path for path, _full_path, _last_modified in paths_to_remove if path in self.memo}
        if paths:
            self.list[:] = [asset for asset in self.list if asset[0] not in paths]
            self.memo.difference_update(paths)
            return

        if paths_to_remove:
            self._raise_not_found([path for path, _full_path, _last_modified in paths_to_remove], bundle)