def test_alter_field_default_doesnt_perform_queries(self):
        """
        No queries are performed if a field default changes and the field's
        not changing from null to non-null.
        """
        with connection.schema_editor() as editor:
            editor.create_model(AuthorWithDefaultHeight)
        old_field = AuthorWithDefaultHeight._meta.get_field("height")
        new_default = old_field.default * 2
        new_field = PositiveIntegerField(null=True, blank=True, default=new_default)
        new_field.set_attributes_from_name("height")
        with connection.schema_editor() as editor, self.assertNumQueries(0):
            editor.alter_field(
                AuthorWithDefaultHeight, old_field, new_field, strict=True
            )