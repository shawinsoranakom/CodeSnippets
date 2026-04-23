def test_referenced_field_without_constraint_rename_inside_atomic_block(self):
        """
        Foreign keys without database level constraint don't prevent the field
        they reference from being renamed in an atomic block.
        """

        class Foo(Model):
            field = CharField(max_length=255, unique=True)

            class Meta:
                app_label = "schema"

        class Bar(Model):
            foo = ForeignKey(Foo, CASCADE, to_field="field", db_constraint=False)

            class Meta:
                app_label = "schema"

        self.isolated_local_models = [Foo, Bar]
        with connection.schema_editor() as editor:
            editor.create_model(Foo)
            editor.create_model(Bar)

        new_field = CharField(max_length=255, unique=True)
        new_field.set_attributes_from_name("renamed")
        with connection.schema_editor(atomic=True) as editor:
            editor.alter_field(Foo, Foo._meta.get_field("field"), new_field)