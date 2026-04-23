def test_alter_model_options(self):
        """Changing a model's options should make a change."""
        changes = self.get_changes([self.author_empty], [self.author_with_options])
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AlterModelOptions"])
        self.assertOperationAttributes(
            changes,
            "testapp",
            0,
            0,
            options={
                "permissions": [("can_hire", "Can hire")],
                "verbose_name": "Authi",
            },
        )

        # Changing them back to empty should also make a change
        changes = self.get_changes([self.author_with_options], [self.author_empty])
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["AlterModelOptions"])
        self.assertOperationAttributes(
            changes, "testapp", 0, 0, name="author", options={}
        )