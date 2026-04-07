def test_alter_field_pk_fk_char_to_int(self):
        app_label = "alter_field_pk_fk_char_to_int"
        project_state = self.apply_operations(
            app_label,
            ProjectState(),
            operations=[
                migrations.CreateModel(
                    name="Parent",
                    fields=[
                        ("id", models.CharField(max_length=255, primary_key=True)),
                    ],
                ),
                migrations.CreateModel(
                    name="Child",
                    fields=[
                        ("id", models.BigAutoField(primary_key=True)),
                        (
                            "parent",
                            models.ForeignKey(
                                f"{app_label}.Parent",
                                on_delete=models.CASCADE,
                            ),
                        ),
                    ],
                ),
            ],
        )
        self.apply_operations(
            app_label,
            project_state,
            operations=[
                migrations.AlterField(
                    model_name="parent",
                    name="id",
                    field=models.BigIntegerField(primary_key=True),
                ),
            ],
        )