def columns(self):
        return tuple(field.column for field in self.fields)