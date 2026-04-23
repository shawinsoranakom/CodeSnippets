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
                queryset = super().get_queryset()._disable_cloning()

            queryset._add_hints(instance=instances[0])
            queryset = queryset.using(queryset._db or self._db)

            rel_obj_attr = self.field.get_local_related_value
            instance_attr = self.field.get_foreign_related_value
            instances_dict = {instance_attr(inst): inst for inst in instances}
            queryset = _filter_prefetch_queryset(queryset, self.field.name, instances)
            # Restore subsequent cloning operations.
            if _cloning_disabled:
                queryset._enable_cloning()

            # Since we just bypassed this class' get_queryset(), we must manage
            # the reverse relation manually.
            for rel_obj in queryset:
                if not self.field.is_cached(rel_obj):
                    instance = instances_dict[rel_obj_attr(rel_obj)]
                    self.field.set_cached_value(rel_obj, instance)
            cache_name = self.field.remote_field.cache_name
            return queryset, rel_obj_attr, instance_attr, False, cache_name, False