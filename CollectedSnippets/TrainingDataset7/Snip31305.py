def test_add_generated_field_with_kt_model(self):
        class GeneratedFieldKTModel(Model):
            data = JSONField()
            status = GeneratedField(
                expression=KT("data__status"),
                output_field=TextField(),
                db_persist=True,
            )

            class Meta:
                app_label = "schema"

        with CaptureQueriesContext(connection) as ctx:
            with connection.schema_editor() as editor:
                editor.create_model(GeneratedFieldKTModel)
        self.assertIs(
            any("None" in query["sql"] for query in ctx.captured_queries),
            False,
        )