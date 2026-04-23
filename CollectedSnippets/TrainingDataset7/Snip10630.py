def _save_table(
        self,
        raw=False,
        cls=None,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        """
        Do the heavy-lifting involved in saving. Update or insert the data
        for a single table.
        """
        meta = cls._meta
        pk_fields = meta.pk_fields
        non_pks_non_generated = [
            f
            for f in meta.local_concrete_fields
            if f not in pk_fields and not f.generated
        ]

        if update_fields:
            non_pks_non_generated = [
                f
                for f in non_pks_non_generated
                if f.name in update_fields or f.attname in update_fields
            ]

        if not self._is_pk_set(meta):
            pk_val = meta.pk.get_pk_value_on_save(self)
            setattr(self, meta.pk.attname, pk_val)
        pk_set = self._is_pk_set(meta)
        if not pk_set and (force_update or update_fields):
            raise ValueError("Cannot force an update in save() with no primary key.")
        updated = False
        # Skip an UPDATE when adding an instance and primary key has a default.
        if (
            not raw
            and not force_insert
            and not force_update
            and self._state.adding
            and all(f.has_default() or f.has_db_default() for f in meta.pk_fields)
        ):
            force_insert = True
        # If possible, try an UPDATE. If that doesn't update anything, do an
        # INSERT.
        if pk_set and not force_insert:
            base_qs = cls._base_manager.using(using)
            values = [
                (
                    f,
                    None,
                    (getattr(self, f.attname) if raw else f.pre_save(self, False)),
                )
                for f in non_pks_non_generated
            ]
            forced_update = update_fields or force_update
            pk_val = self._get_pk_val(meta)
            returning_fields = [
                f
                for f in meta.local_concrete_fields
                if (
                    f.generated
                    and f.referenced_fields.intersection(non_pks_non_generated)
                )
            ]
            for field, _model, value in values:
                if (update_fields is None or field.name in update_fields) and hasattr(
                    value, "resolve_expression"
                ):
                    returning_fields.append(field)
            results = self._do_update(
                base_qs,
                using,
                pk_val,
                values,
                update_fields,
                forced_update,
                returning_fields,
            )
            if updated := bool(results):
                self._assign_returned_values(results[0], returning_fields)
            elif force_update:
                raise self.NotUpdated("Forced update did not affect any rows.")
            elif update_fields:
                raise self.NotUpdated(
                    "Save with update_fields did not affect any rows."
                )
        if not updated:
            if meta.order_with_respect_to:
                # If this is a model with an order_with_respect_to
                # autopopulate the _order field
                field = meta.order_with_respect_to
                filter_args = field.get_filter_kwargs_for_object(self)
                self._order = (
                    cls._base_manager.using(using)
                    .filter(**filter_args)
                    .aggregate(
                        _order__max=Coalesce(
                            ExpressionWrapper(
                                Max("_order") + Value(1), output_field=IntegerField()
                            ),
                            Value(0),
                        ),
                    )["_order__max"]
                )
            insert_fields = [
                f
                for f in meta.local_concrete_fields
                if not f.generated and (pk_set or f is not meta.auto_field)
            ]
            returning_fields = list(meta.db_returning_fields)
            can_return_columns_from_insert = connections[
                using
            ].features.can_return_columns_from_insert
            for field in insert_fields:
                value = (
                    getattr(self, field.attname)
                    if raw
                    else field.pre_save(self, add=True)
                )
                if hasattr(value, "resolve_expression"):
                    if field not in returning_fields:
                        returning_fields.append(field)
                elif (
                    field.db_returning
                    and not can_return_columns_from_insert
                    and not (pk_set and field is meta.auto_field)
                ):
                    returning_fields.remove(field)
            results = self._do_insert(
                cls._base_manager, using, insert_fields, returning_fields, raw
            )
            if results:
                self._assign_returned_values(results[0], returning_fields)
        return updated