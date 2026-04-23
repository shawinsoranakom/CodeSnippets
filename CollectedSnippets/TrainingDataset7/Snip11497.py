def get_prefetch_querysets(self, instances, querysets=None):
        _cloning_disabled = False
        if querysets:
            if len(querysets) != 1:
                raise ValueError(
                    "querysets argument of get_prefetch_querysets() should have a "
                    "length of 1."
                )
            queryset = querysets[0]
        else:
            _cloning_disabled = True
            queryset = self.get_queryset(instance=instances[0])._disable_cloning()

        rel_obj_attr = self.field.get_foreign_related_value
        instance_attr = self.field.get_local_related_value
        instances_dict = {instance_attr(inst): inst for inst in instances}
        remote_field = self.field.remote_field
        related_fields = [
            queryset.query.resolve_ref(field.name).target
            for field in self.field.foreign_related_fields
        ]
        queryset = queryset.filter(
            TupleIn(
                ColPairs(
                    queryset.model._meta.db_table,
                    related_fields,
                    related_fields,
                    self.field,
                ),
                list(instances_dict),
            )
        )
        # There can be only one object prefetched for each instance so clear
        # ordering if the query allows it without side effects.
        queryset.query.clear_ordering()
        # Restore subsequent cloning operations.
        if _cloning_disabled:
            queryset._enable_cloning()

        # Since we're going to assign directly in the cache,
        # we must manage the reverse relation cache manually.
        if not remote_field.multiple:
            for rel_obj in queryset:
                instance = instances_dict[rel_obj_attr(rel_obj)]
                remote_field.set_cached_value(rel_obj, instance)
        return (
            queryset,
            rel_obj_attr,
            instance_attr,
            True,
            self.field.cache_name,
            False,
        )