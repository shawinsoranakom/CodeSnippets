def deconstruct(self):
        # args is always [] so it can be ignored.
        name, path, _, kwargs = super().deconstruct()
        return name, path, self.field_names, kwargs