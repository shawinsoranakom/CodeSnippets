def get_extra_restriction(self, alias, related_alias):
        to_field = self.remote_field.model._meta.get_field(self.to_fields[0])
        from_field = self.model._meta.get_field(self.from_fields[0])
        return StartsWith(to_field.get_col(alias), from_field.get_col(related_alias))