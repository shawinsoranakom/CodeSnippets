def _reverse_one_to_one_field_names(self):
        """
        Return a set of reverse one to one field names pointing to the current
        model.
        """
        return frozenset(
            field.name for field in self.related_objects if field.one_to_one
        )