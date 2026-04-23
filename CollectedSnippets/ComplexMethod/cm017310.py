def values_list(self, *fields, flat=False, named=False):
        if flat and named:
            raise TypeError("'flat' and 'named' can't be used together.")
        if flat:
            if len(fields) > 1:
                raise TypeError(
                    "'flat' is not valid when values_list is called with more than one "
                    "field."
                )
            elif not fields:
                # RemovedInDjango70Warning: When the deprecation ends, replace
                # with:
                # raise TypeError(
                #     "'flat' is not valid when values_list is called with no "
                #     "fields."
                # )
                warnings.warn(
                    "Calling values_list() with no field name and flat=True "
                    "is deprecated. Pass an explicit field name instead, like "
                    "'pk'.",
                    RemovedInDjango70Warning,
                )
                fields = [self.model._meta.concrete_fields[0].attname]

        field_names = {f: False for f in fields if not hasattr(f, "resolve_expression")}
        _fields = []
        expressions = {}
        counter = 1
        for field in fields:
            field_name = field
            expression = None
            if hasattr(field, "resolve_expression"):
                field_name = getattr(
                    field, "default_alias", field.__class__.__name__.lower()
                )
                expression = field
                # For backward compatibility reasons expressions are always
                # prefixed with the counter even if their default alias doesn't
                # collide with field names. Changing this logic could break
                # some usage of named=True.
                seen = True
            elif seen := field_names[field_name]:
                expression = F(field_name)
            if seen:
                field_name_prefix = field_name
                while (field_name := f"{field_name_prefix}{counter}") in field_names:
                    counter += 1
            if expression is not None:
                expressions[field_name] = expression
            field_names[field_name] = True
            _fields.append(field_name)

        clone = self._values(*_fields, **expressions)
        clone._iterable_class = (
            NamedValuesListIterable
            if named
            else FlatValuesListIterable if flat else ValuesListIterable
        )
        return clone