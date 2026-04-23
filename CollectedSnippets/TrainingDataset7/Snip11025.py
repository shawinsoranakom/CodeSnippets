def __eq__(self, other):
        # Needed for @total_ordering
        if isinstance(other, Field):
            return self.creation_counter == other.creation_counter and getattr(
                self, "model", None
            ) == getattr(other, "model", None)
        return NotImplemented