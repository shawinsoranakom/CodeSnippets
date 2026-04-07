def __iter__(self):
        # Cache some things for performance reasons outside the loop.
        db = self.queryset.db
        query = self.queryset.query
        connection = connections[db]
        compiler = connection.ops.compiler("SQLCompiler")(query, connection, db)
        query_iterator = iter(query)

        try:
            (
                model_init_names,
                model_init_pos,
                annotation_fields,
            ) = self.queryset.resolve_model_init_order()
            model_cls = self.queryset.model
            if any(
                f.attname not in model_init_names for f in model_cls._meta.pk_fields
            ):
                raise exceptions.FieldDoesNotExist(
                    "Raw query must include the primary key"
                )
            fields = [self.queryset.model_fields.get(c) for c in self.queryset.columns]
            cols = [f.get_col(f.model._meta.db_table) if f else None for f in fields]
            converters = compiler.get_converters(cols)
            if converters:
                query_iterator = compiler.apply_converters(query_iterator, converters)
            if compiler.has_composite_fields(cols):
                query_iterator = compiler.composite_fields_to_tuples(
                    query_iterator, cols
                )
            fetch_mode = self.queryset._fetch_mode
            peers = []
            for values in query_iterator:
                # Associate fields to values
                model_init_values = [values[pos] for pos in model_init_pos]
                instance = model_cls.from_db(
                    db, model_init_names, model_init_values, fetch_mode=fetch_mode
                )
                if fetch_mode.track_peers:
                    peers.append(weak_ref(instance))
                    instance._state.peers = peers
                if annotation_fields:
                    for column, pos in annotation_fields:
                        setattr(instance, column, values[pos])
                yield instance
        finally:
            # Done iterating the Query. If it has its own cursor, close it.
            if hasattr(query, "cursor") and query.cursor:
                query.cursor.close()