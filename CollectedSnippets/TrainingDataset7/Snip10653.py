def check(cls, **kwargs):
        errors = [
            *cls._check_swappable(),
            *cls._check_model(),
            *cls._check_managers(**kwargs),
        ]
        if not cls._meta.swapped:
            databases = kwargs.get("databases") or []
            errors += [
                *cls._check_fields(**kwargs),
                *cls._check_m2m_through_same_relationship(),
                *cls._check_long_column_names(databases),
                *cls._check_related_fields(),
            ]
            clash_errors = (
                *cls._check_id_field(),
                *cls._check_field_name_clashes(),
                *cls._check_model_name_db_lookup_clashes(),
                *cls._check_property_name_related_field_accessor_clashes(),
                *cls._check_single_primary_key(),
            )
            errors.extend(clash_errors)
            # If there are field name clashes, hide consequent column name
            # clashes.
            if not clash_errors:
                errors.extend(cls._check_column_name_clashes())
            errors += [
                *cls._check_unique_together(),
                *cls._check_indexes(databases),
                *cls._check_ordering(),
                *cls._check_constraints(databases),
                *cls._check_db_table_comment(databases),
                *cls._check_composite_pk(),
            ]

        return errors