def _non_pk_concrete_field_names(self):
        """
        Return a set of the non-pk concrete field names defined on the model.
        """
        names = []
        all_pk_fields = set(self.pk_fields)
        for parent in self.all_parents:
            all_pk_fields.update(parent._meta.pk_fields)
        for field in self.concrete_fields:
            if field not in all_pk_fields:
                names.append(field.name)
                if field.name != field.attname:
                    names.append(field.attname)
        return frozenset(names)