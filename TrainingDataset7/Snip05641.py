def get_lookup_condition(self):
        lookup_conditions = []
        if self.field.empty_strings_allowed:
            lookup_conditions.append((self.field_path, ""))
        if self.field.null:
            lookup_conditions.append((f"{self.field_path}__isnull", True))
        return models.Q.create(lookup_conditions, connector=models.Q.OR)