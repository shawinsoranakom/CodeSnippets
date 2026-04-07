def test_alter_field_with_custom_db_type(self):
        from django.contrib.postgres.fields import ArrayField

        class Foo(Model):
            field = ArrayField(CharField(max_length=255))

            class Meta:
                app_label = "schema"

        with connection.schema_editor() as editor:
            editor.create_model(Foo)
        self.isolated_local_models = [Foo]
        old_field = Foo._meta.get_field("field")
        new_field = ArrayField(CharField(max_length=16))
        new_field.set_attributes_from_name("field")
        new_field.model = Foo
        with connection.schema_editor() as editor:
            editor.alter_field(Foo, old_field, new_field, strict=True)