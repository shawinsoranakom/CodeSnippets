def __eq__(self, other):
        """
        Compare two contexts by comparing theirs 'dicts' attributes.
        """
        if not isinstance(other, BaseContext):
            return NotImplemented
        # flatten dictionaries because they can be put in a different order.
        return self.flatten() == other.flatten()