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
            # Group instances by content types.
            content_type_queries = [
                models.Q.create(
                    [
                        (f"{self.content_type_field_name}__pk", content_type_id),
                        (f"{self.object_id_field_name}__in", {obj.pk for obj in objs}),
                    ]
                )
                for content_type_id, objs in itertools.groupby(
                    sorted(instances, key=lambda obj: self.get_content_type(obj).pk),
                    lambda obj: self.get_content_type(obj).pk,
                )
            ]
            query = models.Q.create(content_type_queries, connector=models.Q.OR)
            # We (possibly) need to convert object IDs to the type of the
            # instances' PK in order to match up instances:
            object_id_converter = instances[0]._meta.pk.to_python
            content_type_id_field_name = "%s_id" % self.content_type_field_name
            queryset = queryset.filter(query)
            # Restore subsequent cloning operations.
            if _cloning_disabled:
                queryset._enable_cloning()
            return (
                queryset,
                lambda relobj: (
                    object_id_converter(getattr(relobj, self.object_id_field_name)),
                    getattr(relobj, content_type_id_field_name),
                ),
                lambda obj: (obj.pk, self.get_content_type(obj).pk),
                False,
                self.prefetch_cache_name,
                False,
            )