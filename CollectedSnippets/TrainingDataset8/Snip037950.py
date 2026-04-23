def update(self, hasher, obj: Any, context: Optional[Context] = None) -> None:
        """Update the provided hasher with the hash of an object."""
        b = self.to_bytes(obj, context)
        hasher.update(b)