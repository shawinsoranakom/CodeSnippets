def test_remove_field_with_model_options(self):
        before_state = [
            ModelState("testapp", "Animal", []),
            ModelState(
                "testapp",
                "Dog",
                fields=[
                    ("name", models.CharField(max_length=100)),
                    (
                        "animal",
                        models.ForeignKey("testapp.Animal", on_delete=models.CASCADE),
                    ),
                ],
                options={
                    "indexes": [
                        models.Index(fields=("animal", "name"), name="animal_name_idx")
                    ],
                    "constraints": [
                        models.UniqueConstraint(
                            fields=("animal", "name"), name="animal_name_idx"
                        ),
                    ],
                },
            ),
        ]
        changes = self.get_changes(before_state, [])
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(
            changes,
            "testapp",
            0,
            [
                "RemoveIndex",
                "RemoveConstraint",
                "RemoveField",
                "DeleteModel",
                "DeleteModel",
            ],
        )