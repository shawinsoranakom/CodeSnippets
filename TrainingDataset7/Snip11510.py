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

        rel_obj_attr = self.related.field.get_local_related_value
        instance_attr = self.related.field.get_foreign_related_value
        instances_dict = {instance_attr(inst): inst for inst in instances}
        query = {"%s__in" % self.related.field.name: instances}
        queryset = queryset.filter(**query)
        # There can be only one object prefetched for each instance so clear
        # ordering if the query allows it without side effects.
        queryset.query.clear_ordering()
        # Restore subsequent cloning operations.
        if _cloning_disabled:
            queryset._enable_cloning()

        # Since we're going to assign directly in the cache,
        # we must manage the reverse relation cache manually.
        for rel_obj in queryset:
            instance = instances_dict[rel_obj_attr(rel_obj)]
            self.related.field.set_cached_value(rel_obj, instance)
        return (
            queryset,
            rel_obj_attr,
            instance_attr,
            True,
            self.related.cache_name,
            False,
        )