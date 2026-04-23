def _check_db_default(self, databases=None, **kwargs):
        from django.db.models.expressions import Value

        if (
            not self.has_db_default()
            or (
                isinstance(self.db_default, Value)
                or not hasattr(self.db_default, "resolve_expression")
            )
            or databases is None
        ):
            return []
        errors = []
        for db in databases:
            if not router.allow_migrate_model(db, self.model):
                continue
            connection = connections[db]

            if not getattr(self._db_default_expression, "allowed_default", False) and (
                connection.features.supports_expression_defaults
            ):
                msg = f"{self.db_default} cannot be used in db_default."
                errors.append(checks.Error(msg, obj=self, id="fields.E012"))

            if not (
                connection.features.supports_expression_defaults
                or "supports_expression_defaults"
                in self.model._meta.required_db_features
            ):
                msg = (
                    f"{connection.display_name} does not support default database "
                    "values with expressions (db_default)."
                )
                errors.append(checks.Error(msg, obj=self, id="fields.E011"))
        return errors