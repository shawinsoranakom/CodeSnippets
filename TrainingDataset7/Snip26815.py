def test_remove_generated_field_before_its_base_field(self):
        initial_state = [
            ModelState(
                "testapp",
                "Author",
                [
                    ("name", models.CharField(max_length=20)),
                    (
                        "upper_name",
                        models.GeneratedField(
                            expression=Upper("name"),
                            db_persist=True,
                            output_field=models.CharField(),
                        ),
                    ),
                ],
            ),
        ]
        updated_state = [ModelState("testapp", "Author", [])]
        changes = self.get_changes(initial_state, updated_state)
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(changes, "testapp", 0, ["RemoveField", "RemoveField"])
        self.assertOperationAttributes(changes, "testapp", 0, 0, name="upper_name")
        self.assertOperationAttributes(changes, "testapp", 0, 1, name="name")