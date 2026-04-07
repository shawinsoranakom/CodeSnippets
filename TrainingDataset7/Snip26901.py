def test_swappable_lowercase(self):
        model_state = ModelState(
            "testapp",
            "Document",
            [
                ("id", models.AutoField(primary_key=True)),
                (
                    "owner",
                    models.ForeignKey(
                        settings.AUTH_USER_MODEL.lower(),
                        models.CASCADE,
                    ),
                ),
            ],
        )
        with isolate_lru_cache(apps.get_swappable_settings_name):
            changes = self.get_changes([], [model_state])
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["CreateModel"])
        self.assertOperationAttributes(changes, "testapp", 0, 0, name="Document")
        self.assertMigrationDependencies(
            changes,
            "testapp",
            0,
            [("__setting__", "AUTH_USER_MODEL")],
        )