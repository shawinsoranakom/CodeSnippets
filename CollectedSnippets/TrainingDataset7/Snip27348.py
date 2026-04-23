def test_remove_field_m2m_with_through(self):
        project_state = self.set_up_test_model("test_rmflmmwt", second_model=True)

        self.assertTableNotExists("test_rmflmmwt_ponystables")
        project_state = self.apply_operations(
            "test_rmflmmwt",
            project_state,
            operations=[
                migrations.CreateModel(
                    "PonyStables",
                    fields=[
                        (
                            "pony",
                            models.ForeignKey("test_rmflmmwt.Pony", models.CASCADE),
                        ),
                        (
                            "stable",
                            models.ForeignKey("test_rmflmmwt.Stable", models.CASCADE),
                        ),
                    ],
                ),
                migrations.AddField(
                    "Pony",
                    "stables",
                    models.ManyToManyField(
                        "Stable",
                        related_name="ponies",
                        through="test_rmflmmwt.PonyStables",
                    ),
                ),
            ],
        )
        self.assertTableExists("test_rmflmmwt_ponystables")

        operations = [
            migrations.RemoveField("Pony", "stables"),
            migrations.DeleteModel("PonyStables"),
        ]
        self.apply_operations("test_rmflmmwt", project_state, operations=operations)