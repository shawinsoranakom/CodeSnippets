def exists(self, name):
        """
        Return True if a file referenced by the given name already exists in
        the storage system, or False if the name is available for a new file.
        """
        raise NotImplementedError(
            "subclasses of Storage must provide an exists() method"
        )