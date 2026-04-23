def handle_m2m_field(self, obj, field):
        """
        Handle a ManyToManyField. Related objects are only serialized as
        references to the object's PK (i.e. the related *data* is not dumped,
        just the relation).
        """
        if field.remote_field.through._meta.auto_created:
            self._start_relational_field(field)
            if self.use_natural_foreign_keys and self._model_supports_natural_key(
                field.remote_field.model
            ):
                # If the objects in the m2m have a natural key, use it
                def handle_m2m(value):
                    if natural := self._resolve_natural_key(value):
                        # Iterable natural keys are rolled out as subelements
                        self.xml.startElement("object", {})
                        for key_value in natural:
                            self.xml.startElement("natural", {})
                            if key_value is None:
                                self.xml.addQuickElement("None")
                            else:
                                self.xml.characters(str(key_value))
                            self.xml.endElement("natural")
                        self.xml.endElement("object")
                    else:
                        self.xml.addQuickElement("object", attrs={"pk": str(value.pk)})

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

                def handle_m2m(value):
                    # Put each object on its own line.
                    self.indent(self.indent_level + 1)
                    self.xml.addQuickElement("object", attrs={"pk": str(value.pk)})

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
            relobj = None
            for relobj in m2m_iter:
                handle_m2m(relobj)
            if relobj:
                # If there are related objects (which appear each on their own
                # line), put the closing </field> on the next line.
                self.indent(self.indent_level)
            self.xml.endElement("field")
            self.indent_level -= 1