def test_invalid_generated_field_persistency_change(self):
        app_label = "test_igfpc"
        project_state = self.set_up_test_model(app_label)
        operations = [
            migrations.AddField(
                "Pony",
                "modified_pink",
                models.GeneratedField(
                    expression=F("pink") + 2,
                    output_field=models.IntegerField(),
                    db_persist=True,
                ),
            ),
            migrations.AlterField(
                "Pony",
                "modified_pink",
                models.GeneratedField(
                    expression=F("pink") + 2,
                    output_field=models.IntegerField(),
                    db_persist=False,
                ),
            ),
        ]
        msg = (
            "Modifying GeneratedFields is not supported - the field "
            f"{app_label}.Pony.modified_pink must be removed and re-added with the "
            "new definition."
        )
        with self.assertRaisesMessage(ValueError, msg):
            self.apply_operations(app_label, project_state, operations)