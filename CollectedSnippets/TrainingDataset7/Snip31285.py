def test_text_field_with_db_index_to_fk(self):
        # Create the table
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(AuthorTextFieldWithIndex)
        # Change TextField to FK
        old_field = AuthorTextFieldWithIndex._meta.get_field("text_field")
        new_field = ForeignKey(Author, CASCADE, blank=True)
        new_field.set_attributes_from_name("text_field")
        with connection.schema_editor() as editor:
            editor.alter_field(
                AuthorTextFieldWithIndex, old_field, new_field, strict=True
            )
        self.assertForeignKeyExists(
            AuthorTextFieldWithIndex, "text_field_id", "schema_author"
        )