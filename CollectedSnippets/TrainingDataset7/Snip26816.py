def test_remove_generated_field_before_multiple_base_fields(self):
        initial_state = [
            ModelState(
                "testapp",
                "Author",
                [
                    ("first_name", models.CharField(max_length=20)),
                    ("last_name", models.CharField(max_length=20)),
                    (
                        "full_name",
                        models.GeneratedField(
                            expression=Concat("first_name", "last_name"),
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
        self.assertOperationTypes(
            changes, "testapp", 0, ["RemoveField", "RemoveField", "RemoveField"]
        )
        self.assertOperationAttributes(changes, "testapp", 0, 0, name="full_name")
        self.assertOperationAttributes(changes, "testapp", 0, 1, name="first_name")
        self.assertOperationAttributes(changes, "testapp", 0, 2, name="last_name")