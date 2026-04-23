def handle_m2m_field(self, obj, field):
        if field.remote_field.through._meta.auto_created:
            if self.use_natural_foreign_keys and self._model_supports_natural_key(
                field.remote_field.model
            ):

                def m2m_value(value):
                    if natural := value.natural_key():
                        return natural
                    else:
                        return self._value_from_field(value, value._meta.pk)

                def queryset_iterator(obj, field):
                    attr = getattr(obj, field.name)
                    chunk_size = (
                        2000 if getattr(attr, "prefetch_cache_name", None) else None
                    )
                    query_set = attr.all()
                    if not query_set.totally_ordered:
                        current_ordering = (
                            query_set.query.order_by
                            or query_set.model._meta.ordering
                            or []
                        )
                        query_set = query_set.order_by(*current_ordering, "pk")
                    return query_set.iterator(chunk_size)

            else:

                def m2m_value(value):
                    return self._value_from_field(value, value._meta.pk)

                def queryset_iterator(obj, field):
                    query_set = getattr(obj, field.name).select_related(None).only("pk")
                    if not query_set.totally_ordered:
                        current_ordering = (
                            query_set.query.order_by
                            or query_set.model._meta.ordering
                            or []
                        )
                        query_set = query_set.order_by(*current_ordering, "pk")
                    chunk_size = 2000 if query_set._prefetch_related_lookups else None
                    return query_set.iterator(chunk_size=chunk_size)

            m2m_iter = getattr(obj, "_prefetched_objects_cache", {}).get(
                field.name,
                queryset_iterator(obj, field),
            )
            self._current[field.name] = [m2m_value(related) for related in m2m_iter]