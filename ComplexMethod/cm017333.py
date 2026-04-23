def refresh_from_db(self, using=None, fields=None, from_queryset=None):
        """
        Reload field values from the database.

        By default, the reloading happens from the database this instance was
        loaded from, or by the read router if this instance wasn't loaded from
        any database. The using parameter will override the default.

        Fields can be used to specify which fields to reload. The fields
        should be an iterable of field attnames. If fields is None, then
        all non-deferred fields are reloaded.

        When fetching deferred fields for a single instance (the FETCH_ONE
        fetch mode), the deferred loading uses this method.
        """
        if fields is None:
            self._prefetched_objects_cache = {}
        else:
            prefetched_objects_cache = getattr(self, "_prefetched_objects_cache", ())
            fields = set(fields)
            for field in fields.copy():
                if field in prefetched_objects_cache:
                    del prefetched_objects_cache[field]
                    fields.remove(field)
            if not fields:
                return
            if any(LOOKUP_SEP in f for f in fields):
                raise ValueError(
                    'Found "%s" in fields argument. Relations and transforms '
                    "are not allowed in fields." % LOOKUP_SEP
                )

        if from_queryset is None:
            hints = {"instance": self}
            from_queryset = self.__class__._base_manager.db_manager(using, hints=hints)
        elif using is not None:
            from_queryset = from_queryset.using(using)

        db_instance_qs = from_queryset.filter(pk=self.pk)

        # Use provided fields, if not set then reload all non-deferred fields.
        deferred_fields = self.get_deferred_fields()
        if fields is not None:
            db_instance_qs = db_instance_qs.only(*fields)
        elif deferred_fields:
            db_instance_qs = db_instance_qs.only(
                *{
                    f.attname
                    for f in self._meta.concrete_fields
                    if f.attname not in deferred_fields
                }
            )

        db_instance = db_instance_qs.get()
        non_loaded_fields = db_instance.get_deferred_fields()
        for field in self._meta.fields:
            if field.attname in non_loaded_fields:
                # This field wasn't refreshed - skip ahead.
                continue
            if field.concrete:
                setattr(self, field.attname, getattr(db_instance, field.attname))
            # Clear or copy cached foreign keys.
            if field.is_relation:
                if field.is_cached(db_instance):
                    field.set_cached_value(self, field.get_cached_value(db_instance))
                elif field.is_cached(self):
                    field.delete_cached_value(self)

        # Clear cached relations.
        for rel in self._meta.related_objects:
            if (fields is None or rel.name in fields) and rel.is_cached(self):
                rel.delete_cached_value(self)

        # Clear cached private relations.
        for field in self._meta.private_fields:
            if (
                (fields is None or field.name in fields)
                and field.is_relation
                and field.is_cached(self)
            ):
                field.delete_cached_value(self)

        self._state.db = db_instance._state.db