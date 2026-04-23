def __getitem__(self, key):
        """Allow header lookup using underscores in place of hyphens."""
        return super().__getitem__(key.replace("_", "-"))