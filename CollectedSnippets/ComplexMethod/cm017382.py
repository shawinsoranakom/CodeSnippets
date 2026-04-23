def _check_supported(self, databases):
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
            if not (
                connection.features.supports_virtual_generated_columns
                or "supports_stored_generated_columns"
                in self.model._meta.required_db_features
            ) and not (
                connection.features.supports_stored_generated_columns
                or "supports_virtual_generated_columns"
                in self.model._meta.required_db_features
            ):
                errors.append(
                    checks.Error(
                        f"{connection.display_name} does not support GeneratedFields.",
                        obj=self,
                        id="fields.E220",
                    )
                )
        return errors