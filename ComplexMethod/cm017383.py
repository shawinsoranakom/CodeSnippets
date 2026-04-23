def _check_persistence(self, databases):
        errors = []
        for db in databases:
            if not router.allow_migrate_model(db, self.model):
                continue
            connection = connections[db]
            if (
                self.model._meta.required_db_vendor
                and self.model._meta.required_db_vendor != connection.vendor
            ):
                continue
            if not self.db_persist and not (
                connection.features.supports_virtual_generated_columns
                or "supports_virtual_generated_columns"
                in self.model._meta.required_db_features
            ):
                errors.append(
                    checks.Error(
                        f"{connection.display_name} does not support non-persisted "
                        "GeneratedFields.",
                        obj=self,
                        id="fields.E221",
                        hint="Set db_persist=True on the field.",
                    )
                )
            if self.db_persist and not (
                connection.features.supports_stored_generated_columns
                or "supports_stored_generated_columns"
                in self.model._meta.required_db_features
            ):
                errors.append(
                    checks.Error(
                        f"{connection.display_name} does not support persisted "
                        "GeneratedFields.",
                        obj=self,
                        id="fields.E222",
                        hint="Set db_persist=False on the field.",
                    )
                )
        return errors