def test_default_related_name_option(self):
        model_state = ModelState(
            "app",
            "model",
            [
                ("id", models.AutoField(primary_key=True)),
            ],
            options={"default_related_name": "related_name"},
        )
        changes = self.get_changes([], [model_state])
        self.assertNumberMigrations(changes, "app", 1)
        self.assertOperationTypes(changes, "app", 0, ["CreateModel"])
        self.assertOperationAttributes(
            changes,
            "app",
            0,
            0,
            name="model",
            options={"default_related_name": "related_name"},
        )
        altered_model_state = ModelState(
            "app",
            "Model",
            [
                ("id", models.AutoField(primary_key=True)),
            ],
        )
        changes = self.get_changes([model_state], [altered_model_state])
        self.assertNumberMigrations(changes, "app", 1)
        self.assertOperationTypes(changes, "app", 0, ["AlterModelOptions"])
        self.assertOperationAttributes(changes, "app", 0, 0, name="model", options={})