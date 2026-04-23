def test_alter_primary_key_quoted_db_table(self):
        class Foo(Model):
            class Meta:
                app_label = "schema"
                db_table = '"foo"'

        with connection.schema_editor() as editor:
            editor.create_model(Foo)
        self.isolated_local_models = [Foo]
        old_field = Foo._meta.get_field("id")
        new_field = BigAutoField(primary_key=True)
        new_field.model = Foo
        new_field.set_attributes_from_name("id")
        with connection.schema_editor() as editor:
            editor.alter_field(Foo, old_field, new_field, strict=True)
        Foo.objects.create()