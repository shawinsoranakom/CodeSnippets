def test_add_generated_field_contains(self):
        class GeneratedFieldContainsModel(Model):
            text = TextField(default="foo")
            generated = GeneratedField(
                expression=Concat("text", Value("%")),
                db_persist=True,
                output_field=TextField(),
            )

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(GeneratedFieldContainsModel)

        field = GeneratedField(
            expression=Q(text__contains="foo"),
            db_persist=True,
            output_field=BooleanField(),
        )
        field.contribute_to_class(GeneratedFieldContainsModel, "contains_foo")

        with connection.schema_editor() as editor:
            editor.add_field(GeneratedFieldContainsModel, field)

        obj = GeneratedFieldContainsModel.objects.create()
        obj.refresh_from_db()
        self.assertEqual(obj.text, "foo")
        self.assertEqual(obj.generated, "foo%")
        self.assertIs(obj.contains_foo, True)