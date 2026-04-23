def test_remove_field_m2m(self):
        project_state = self.set_up_test_model("test_rmflmm", second_model=True)

        project_state = self.apply_operations(
            "test_rmflmm",
            project_state,
            operations=[
                migrations.AddField(
                    "Pony",
                    "stables",
                    models.ManyToManyField("Stable", related_name="ponies"),
                )
            ],
        )
        self.assertTableExists("test_rmflmm_pony_stables")

        with_field_state = project_state.clone()
        operations = [migrations.RemoveField("Pony", "stables")]
        project_state = self.apply_operations(
            "test_rmflmm", project_state, operations=operations
        )
        self.assertTableNotExists("test_rmflmm_pony_stables")

        # And test reversal
        self.unapply_operations("test_rmflmm", with_field_state, operations=operations)
        self.assertTableExists("test_rmflmm_pony_stables")