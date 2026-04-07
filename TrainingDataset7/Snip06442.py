def get_foreign_related_value(self, instance):
        # We (possibly) need to convert object IDs to the type of the
        # instances' PK in order to match up instances during prefetching.
        return tuple(
            foreign_field.to_python(val)
            for foreign_field, val in zip(
                self.foreign_related_fields,
                self.get_instance_value_for_fields(instance, self.local_related_fields),
            )
        )