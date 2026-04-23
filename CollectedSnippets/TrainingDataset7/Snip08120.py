def find(self, path, find_all=False):
        """
        Look for files in the default file storage, if it's local.
        """
        try:
            self.storage.path("")
        except NotImplementedError:
            pass
        else:
            if self.storage.location not in searched_locations:
                searched_locations.append(self.storage.location)
            if self.storage.exists(path):
                match = self.storage.path(path)
                if find_all:
                    match = [match]
                return match
        return []