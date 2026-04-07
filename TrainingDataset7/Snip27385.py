def test_rename_referenced_field_state_forward(self):
        state = ProjectState()
        state.add_model(
            ModelState(
                "app",
                "Model",
                [
                    ("id", models.AutoField(primary_key=True)),
                    ("field", models.IntegerField(unique=True)),
                ],
            )
        )
        state.add_model(
            ModelState(
                "app",
                "OtherModel",
                [
                    ("id", models.AutoField(primary_key=True)),
                    (
                        "fk",
                        models.ForeignKey("Model", models.CASCADE, to_field="field"),
                    ),
                    (
                        "fo",
                        models.ForeignObject(
                            "Model",
                            models.CASCADE,
                            from_fields=("fk",),
                            to_fields=("field",),
                        ),
                    ),
                ],
            )
        )
        operation = migrations.RenameField("Model", "field", "renamed")
        new_state = state.clone()
        operation.state_forwards("app", new_state)
        self.assertEqual(
            new_state.models["app", "othermodel"].fields["fk"].remote_field.field_name,
            "renamed",
        )
        self.assertEqual(
            new_state.models["app", "othermodel"].fields["fk"].from_fields, ["self"]
        )
        self.assertEqual(
            new_state.models["app", "othermodel"].fields["fk"].to_fields, ("renamed",)
        )
        self.assertEqual(
            new_state.models["app", "othermodel"].fields["fo"].from_fields, ("fk",)
        )
        self.assertEqual(
            new_state.models["app", "othermodel"].fields["fo"].to_fields, ("renamed",)
        )
        operation = migrations.RenameField("OtherModel", "fk", "renamed_fk")
        new_state = state.clone()
        operation.state_forwards("app", new_state)
        self.assertEqual(
            new_state.models["app", "othermodel"]
            .fields["renamed_fk"]
            .remote_field.field_name,
            "renamed",
        )
        self.assertEqual(
            new_state.models["app", "othermodel"].fields["renamed_fk"].from_fields,
            ("self",),
        )
        self.assertEqual(
            new_state.models["app", "othermodel"].fields["renamed_fk"].to_fields,
            ("renamed",),
        )
        self.assertEqual(
            new_state.models["app", "othermodel"].fields["fo"].from_fields,
            ("renamed_fk",),
        )
        self.assertEqual(
            new_state.models["app", "othermodel"].fields["fo"].to_fields, ("renamed",)
        )