def __lt__(self, other):
        # This is needed because bisect does not take a comparison function.
        # Order by creation_counter first for backward compatibility.
        if isinstance(other, Field):
            if (
                self.creation_counter != other.creation_counter
                or not hasattr(self, "model")
                and not hasattr(other, "model")
            ):
                return self.creation_counter < other.creation_counter
            elif hasattr(self, "model") != hasattr(other, "model"):
                return not hasattr(self, "model")  # Order no-model fields first
            else:
                # creation_counter's are equal, compare only models.
                return (self.model._meta.app_label, self.model._meta.model_name) < (
                    other.model._meta.app_label,
                    other.model._meta.model_name,
                )
        return NotImplemented