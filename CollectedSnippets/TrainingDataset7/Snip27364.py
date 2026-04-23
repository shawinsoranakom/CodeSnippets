def test_alter_field_foreignobject_noop(self):
        app_label = "test_alflfo_noop"
        project_state = self.set_up_test_model(app_label)
        project_state = self.apply_operations(
            app_label,
            project_state,
            [
                migrations.CreateModel(
                    "Rider",
                    fields=[
                        ("pony_id", models.IntegerField()),
                        (
                            "pony",
                            models.ForeignObject(
                                f"{app_label}.Pony",
                                models.CASCADE,
                                from_fields=("pony_id",),
                                to_fields=("id",),
                            ),
                        ),
                    ],
                ),
            ],
        )
        operation = migrations.AlterField(
            "Rider",
            "pony",
            models.ForeignObject(
                f"{app_label}.Pony",
                models.CASCADE,
                from_fields=("pony_id",),
                to_fields=("id",),
                null=True,
            ),
        )
        new_state = project_state.clone()
        operation.state_forwards(app_label, new_state)
        with (
            CaptureQueriesContext(connection) as ctx,
            connection.schema_editor() as editor,
        ):
            operation.database_forwards(app_label, editor, project_state, new_state)
        self.assertIs(
            any("ALTER" in query["sql"] for query in ctx.captured_queries), False
        )