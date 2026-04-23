def fields(self):
        meta = self.model._meta
        return tuple(meta.get_field(field_name) for field_name in self.field_names)