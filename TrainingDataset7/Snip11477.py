def contribute_to_related_class(self, cls, related):
        # Internal M2Ms (i.e., those with a related name ending with '+')
        # and swapped models don't get a related descriptor.
        if not self.remote_field.hidden and not related.related_model._meta.swapped:
            setattr(
                cls,
                related.accessor_name,
                ManyToManyDescriptor(self.remote_field, reverse=True),
            )

        # Set up the accessors for the column names on the m2m table.
        self.m2m_column_name = partial(self._get_m2m_attr, related, "column")
        self.m2m_reverse_name = partial(self._get_m2m_reverse_attr, related, "column")

        self.m2m_field_name = partial(self._get_m2m_attr, related, "name")
        self.m2m_reverse_field_name = partial(
            self._get_m2m_reverse_attr, related, "name"
        )

        get_m2m_rel = partial(self._get_m2m_attr, related, "remote_field")
        self.m2m_target_field_name = lambda: get_m2m_rel().field_name
        get_m2m_reverse_rel = partial(
            self._get_m2m_reverse_attr, related, "remote_field"
        )
        self.m2m_reverse_target_field_name = lambda: get_m2m_reverse_rel().field_name