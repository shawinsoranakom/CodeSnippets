def _check_db_comment(self, databases=None, **kwargs):
        if not self.db_comment or not databases:
            return []
        errors = []
        for db in databases:
            if not router.allow_migrate_model(db, self.model):
                continue
            connection = connections[db]
            if not (
                connection.features.supports_comments
                or "supports_comments" in self.model._meta.required_db_features
            ):
                errors.append(
                    checks.Warning(
                        f"{connection.display_name} does not support comments on "
                        f"columns (db_comment).",
                        obj=self,
                        id="fields.W163",
                    )
                )
        return errors