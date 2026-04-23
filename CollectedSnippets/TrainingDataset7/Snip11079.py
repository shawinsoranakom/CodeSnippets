def _check_db_collation(self, databases):
        errors = []
        for db in databases:
            if not router.allow_migrate_model(db, self.model):
                continue
            connection = connections[db]
            if not (
                self.db_collation is None
                or "supports_collation_on_charfield"
                in self.model._meta.required_db_features
                or connection.features.supports_collation_on_charfield
            ):
                errors.append(
                    checks.Error(
                        "%s does not support a database collation on "
                        "CharFields." % connection.display_name,
                        obj=self,
                        id="fields.E190",
                    ),
                )
        return errors