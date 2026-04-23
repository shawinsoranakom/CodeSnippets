def _check_references(self, model, references):
        from django.db.models.fields.composite import CompositePrimaryKey

        errors = []
        fields = set()
        for field_name, *lookups in references:
            # pk is an alias that won't be found by opts.get_field().
            if field_name != "pk" or isinstance(model._meta.pk, CompositePrimaryKey):
                fields.add(field_name)
            if not lookups:
                # If it has no lookups it cannot result in a JOIN.
                continue
            try:
                if field_name == "pk":
                    field = model._meta.pk
                else:
                    field = model._meta.get_field(field_name)
                if not field.is_relation or field.many_to_many or field.one_to_many:
                    continue
            except FieldDoesNotExist:
                continue
            # JOIN must happen at the first lookup.
            first_lookup = lookups[0]
            if (
                hasattr(field, "get_transform")
                and hasattr(field, "get_lookup")
                and field.get_transform(first_lookup) is None
                and field.get_lookup(first_lookup) is None
            ):
                errors.append(
                    checks.Error(
                        "'constraints' refers to the joined field '%s'."
                        % LOOKUP_SEP.join([field_name, *lookups]),
                        obj=model,
                        id="models.E041",
                    )
                )
        errors.extend(model._check_local_fields(fields, "constraints"))
        return errors