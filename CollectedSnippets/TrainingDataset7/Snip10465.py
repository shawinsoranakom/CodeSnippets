def serialize(self):
        partial_name = self.value.__class__.__name__
        return DeconstructibleSerializer.serialize_deconstructed(
            f"functools.{partial_name}",
            (self.value.func, *self.value.args),
            self.value.keywords,
        )