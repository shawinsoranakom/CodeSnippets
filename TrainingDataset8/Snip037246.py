def __eq__(self, other) -> bool:
        """Equality operator."""
        return (
            isinstance(other, CustomComponent)
            and self.name == other.name
            and self.path == other.path
            and self.url == other.url
        )