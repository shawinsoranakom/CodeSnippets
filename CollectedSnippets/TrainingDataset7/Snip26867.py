def test_remove_field_with_remove_index_or_constraint_dependency(self):
        before_state = [
            ModelState("testapp", "Category", []),
            ModelState(
                "testapp",
                "Model",
                fields=[
                    ("date", models.DateField(auto_now=True)),
                    (
                        "category",
                        models.ForeignKey(
                            "testapp.Category", models.SET_NULL, null=True
                        ),
                    ),
                ],
                options={
                    "constraints": [
                        models.UniqueConstraint(
                            fields=("date", "category"), name="unique_category_for_date"
                        ),
                    ]
                },
            ),
        ]
        changes = self.get_changes(
            before_state,
            [
                ModelState(
                    "testapp",
                    "Model",
                    fields=[
                        ("date", models.DateField(auto_now=True)),
                    ],
                ),
            ],
        )
        # Right number/type of migrations?
        self.assertNumberMigrations(changes, "testapp", 1)
        self.assertOperationTypes(
            changes,
            "testapp",
            0,
            ["RemoveConstraint", "RemoveField", "DeleteModel"],
        )