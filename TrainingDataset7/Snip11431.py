def _check_on_delete_db_support(self, on_delete, feature_flag, databases):
        for db in databases:
            if not router.allow_migrate_model(db, self.model):
                continue
            connection = connections[db]
            if feature_flag in self.model._meta.required_db_features or getattr(
                connection.features, feature_flag
            ):
                continue
            no_db_option_name = on_delete.__name__.removeprefix("DB_")
            yield checks.Error(
                f"{connection.display_name} does not support a {on_delete.__name__}.",
                hint=f"Change the on_delete rule to {no_db_option_name}.",
                obj=self,
                id="fields.E324",
            )