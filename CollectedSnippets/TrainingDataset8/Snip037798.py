def update(self, hasher, obj: Any) -> None:
        """Update the provided hasher with the hash of an object."""
        b = self.to_bytes(obj)
        hasher.update(b)