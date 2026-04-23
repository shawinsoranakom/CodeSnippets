def save(
        self,
        *,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        """
        Save the current instance. Override this in a subclass if you want to
        control the saving process.

        The 'force_insert' and 'force_update' parameters can be used to insist
        that the "save" must be an SQL insert or update (or equivalent for
        non-SQL backends), respectively. Normally, they should not be set.
        """

        self._prepare_related_fields_for_save(operation_name="save")

        using = using or router.db_for_write(self.__class__, instance=self)
        if force_insert and (force_update or update_fields):
            raise ValueError("Cannot force both insert and updating in model saving.")

        deferred_non_generated_fields = {
            f.attname
            for f in self._meta.concrete_fields
            if f.attname not in self.__dict__ and f.generated is False
        }
        if update_fields is not None:
            # If update_fields is empty, skip the save. We do also check for
            # no-op saves later on for inheritance cases. This bailout is
            # still needed for skipping signal sending.
            if not update_fields:
                return

            update_fields = frozenset(update_fields)
            field_names = self._meta._non_pk_concrete_field_names
            not_updatable_fields = update_fields.difference(field_names)

            if not_updatable_fields:
                raise ValueError(
                    "The following fields do not exist in this model, are m2m "
                    "fields, primary keys, or are non-concrete fields: %s"
                    % ", ".join(not_updatable_fields)
                )

        # If saving to the same database, and this model is deferred, then
        # automatically do an "update_fields" save on the loaded fields.
        elif (
            not force_insert
            and deferred_non_generated_fields
            and using == self._state.db
            and self._is_pk_set()
        ):
            field_names = set()
            pk_fields = self._meta.pk_fields
            for field in self._meta.concrete_fields:
                if field not in pk_fields and not hasattr(field, "through"):
                    field_names.add(field.attname)
            loaded_fields = field_names.difference(deferred_non_generated_fields)
            if loaded_fields:
                update_fields = frozenset(loaded_fields)

        self.save_base(
            using=using,
            force_insert=force_insert,
            force_update=force_update,
            update_fields=update_fields,
        )