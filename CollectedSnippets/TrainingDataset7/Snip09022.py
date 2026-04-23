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