def test_alter_generated_field(self):
        class GeneratedFieldIndexedModel(Model):
            number = IntegerField(default=1)
            generated = GeneratedField(
                expression=F("number") + 1,
                db_persist=True,
                output_field=IntegerField(),
            )

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(GeneratedFieldIndexedModel)

        old_field = GeneratedFieldIndexedModel._meta.get_field("generated")
        new_field = GeneratedField(
            expression=F("number") + 1,
            db_persist=True,
            db_index=True,
            output_field=IntegerField(),
        )
        new_field.contribute_to_class(GeneratedFieldIndexedModel, "generated")

        with connection.schema_editor() as editor:
            editor.alter_field(GeneratedFieldIndexedModel, old_field, new_field)

        self.assertIn(
            "generated", self.get_indexes(GeneratedFieldIndexedModel._meta.db_table)
        )