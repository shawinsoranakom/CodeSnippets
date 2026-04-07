def _check_db_table_comment(cls, databases):
        if not cls._meta.db_table_comment:
            return []
        errors = []
        for db in databases:
            if not router.allow_migrate_model(db, cls):
                continue
            connection = connections[db]
            if not (
                connection.features.supports_comments
                or "supports_comments" in cls._meta.required_db_features
            ):
                errors.append(
                    checks.Warning(
                        f"{connection.display_name} does not support comments on "
                        f"tables (db_table_comment).",
                        obj=cls,
                        id="models.W046",
                    )
                )
        return errors