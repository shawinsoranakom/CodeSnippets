def delete(self, name):
        """
        Delete the specified file from the storage system.
        """
        raise NotImplementedError(
            "subclasses of Storage must provide a delete() method"
        )