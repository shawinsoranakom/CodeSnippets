def test_alter_array_field_decrease_nested_base_field_length(self):
        from django.contrib.postgres.fields import ArrayField

        class ArrayModel(Model):
            field = ArrayField(ArrayField(CharField(max_length=16)))

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(ArrayModel)
        self.isolated_local_models = [ArrayModel]
        ArrayModel.objects.create(field=[["x" * 16]])
        old_field = ArrayModel._meta.get_field("field")
        new_field = ArrayField(ArrayField(CharField(max_length=15)))
        new_field.set_attributes_from_name("field")
        new_field.model = ArrayModel
        with connection.schema_editor() as editor:
            msg = "value too long for type character varying(15)"
            with self.assertRaisesMessage(DataError, msg):
                editor.alter_field(ArrayModel, old_field, new_field, strict=True)