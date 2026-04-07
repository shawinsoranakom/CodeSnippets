def serialize(self):
        return self.serialize_deconstructed(*self.value.deconstruct())