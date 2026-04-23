def test_alter_field_m2m(self):
        project_state = self.set_up_test_model("test_alflmm", second_model=True)

        project_state = self.apply_operations(
            "test_alflmm",
            project_state,
            operations=[
                migrations.AddField(
                    "Pony",
                    "stables",
                    models.ManyToManyField("Stable", related_name="ponies"),
                )
            ],
        )
        Pony = project_state.apps.get_model("test_alflmm", "Pony")
        self.assertFalse(Pony._meta.get_field("stables").blank)

        project_state = self.apply_operations(
            "test_alflmm",
            project_state,
            operations=[
                migrations.AlterField(
                    "Pony",
                    "stables",
                    models.ManyToManyField(
                        to="Stable", related_name="ponies", blank=True
                    ),
                )
            ],
        )
        Pony = project_state.apps.get_model("test_alflmm", "Pony")
        self.assertTrue(Pony._meta.get_field("stables").blank)