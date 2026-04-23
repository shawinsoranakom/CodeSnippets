def test_add_generated_boolean_field(self):
        class GeneratedBooleanFieldModel(Model):
            value = IntegerField(null=True)
            has_value = GeneratedField(
                expression=Q(value__isnull=False),
                output_field=BooleanField(),
                db_persist=False,
            )

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(GeneratedBooleanFieldModel)
        obj = GeneratedBooleanFieldModel.objects.create()
        self.assertIs(obj.has_value, False)
        obj = GeneratedBooleanFieldModel.objects.create(value=1)
        self.assertIs(obj.has_value, True)