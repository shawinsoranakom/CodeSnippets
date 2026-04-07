def test_create_with_through_model(self):
        """
        Adding a m2m with a through model and the models that use it should be
        ordered correctly.
        """
        changes = self.get_changes(
            [], [self.author_with_m2m_through, self.publisher, self.contract]
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(
            changes,
            "testapp",
            0,
            [
                "CreateModel",
                "CreateModel",
                "CreateModel",
                "AddField",
            ],
        )
        self.assertOperationAttributes(changes, "testapp", 0, 0, name="Author")
        self.assertOperationAttributes(changes, "testapp", 0, 1, name="Publisher")
        self.assertOperationAttributes(changes, "testapp", 0, 2, name="Contract")
        self.assertOperationAttributes(
            changes, "testapp", 0, 3, model_name="author", name="publishers"
        )