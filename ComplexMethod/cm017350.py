def _check_related_fields(cls):
        has_db_variant = False
        has_python_variant = False
        for rel in cls._meta.get_fields():
            if rel.related_model:
                if not (on_delete := getattr(rel.remote_field, "on_delete", None)):
                    continue
                if isinstance(on_delete, DatabaseOnDelete):
                    has_db_variant = True
                elif on_delete != DO_NOTHING:
                    has_python_variant = True
                if has_db_variant and has_python_variant:
                    return [
                        checks.Error(
                            "The model cannot have related fields with both "
                            "database-level and Python-level on_delete variants.",
                            obj=cls,
                            id="models.E050",
                        )
                    ]
        return []