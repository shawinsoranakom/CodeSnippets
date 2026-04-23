def __iter__(self):
        queryset = self.queryset
        db = queryset.db
        compiler = queryset.query.get_compiler(using=db)
        fetch_mode = queryset._fetch_mode
        # Execute the query. This will also fill compiler.select, klass_info,
        # and annotations.
        results = compiler.execute_sql(
            chunked_fetch=self.chunked_fetch, chunk_size=self.chunk_size
        )
        select, klass_info, annotation_col_map = (
            compiler.select,
            compiler.klass_info,
            compiler.annotation_col_map,
        )
        model_cls = klass_info["model"]
        select_fields = klass_info["select_fields"]
        model_fields_start, model_fields_end = select_fields[0], select_fields[-1] + 1
        init_list = [
            f[0].target.attname for f in select[model_fields_start:model_fields_end]
        ]
        related_populators = get_related_populators(klass_info, select, db, fetch_mode)
        known_related_objects = [
            (
                field,
                related_objs,
                attnames := [
                    (
                        field.attname
                        if from_field == "self"
                        else queryset.model._meta.get_field(from_field).attname
                    )
                    for from_field in field.from_fields
                ],
                operator.attrgetter(*attnames),
            )
            for field, related_objs in queryset._known_related_objects.items()
        ]
        peers = []
        for row in compiler.results_iter(results):
            obj = model_cls.from_db(
                db,
                init_list,
                row[model_fields_start:model_fields_end],
                fetch_mode=fetch_mode,
            )
            if fetch_mode.track_peers:
                peers.append(weak_ref(obj))
                obj._state.peers = peers
            for rel_populator in related_populators:
                rel_populator.populate(row, obj)
            if annotation_col_map:
                for attr_name, col_pos in annotation_col_map.items():
                    setattr(obj, attr_name, row[col_pos])

            # Add the known related objects to the model.
            for field, rel_objs, rel_attnames, rel_getter in known_related_objects:
                # Avoid overwriting objects loaded by, e.g., select_related().
                if field.is_cached(obj):
                    continue
                # Avoid fetching potentially deferred attributes that would
                # result in unexpected queries.
                if any(attname not in obj.__dict__ for attname in rel_attnames):
                    continue
                rel_obj_id = rel_getter(obj)
                try:
                    rel_obj = rel_objs[rel_obj_id]
                except KeyError:
                    pass  # May happen in qs1 | qs2 scenarios.
                else:
                    setattr(obj, field.name, rel_obj)

            yield obj