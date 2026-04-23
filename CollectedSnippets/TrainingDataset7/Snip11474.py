def _get_m2m_attr(self, related, attr):
        """
        Function that can be curried to provide the source accessor or DB
        column name for the m2m table.
        """
        cache_attr = "_m2m_%s_cache" % attr
        if hasattr(self, cache_attr):
            return getattr(self, cache_attr)
        if self.remote_field.through_fields is not None:
            link_field_name = self.remote_field.through_fields[0]
        else:
            link_field_name = None
        for f in self.remote_field.through._meta.fields:
            if (
                f.is_relation
                and f.remote_field.model == related.related_model
                and (link_field_name is None or link_field_name == f.name)
            ):
                setattr(self, cache_attr, getattr(f, attr))
                return getattr(self, cache_attr)