def serialize(self):
        attr_name, path, args, kwargs = self.value.deconstruct()
        return self.serialize_deconstructed(path, args, kwargs)