def test_char_field_with_db_index_to_fk(self):
        # Create the table
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(AuthorCharFieldWithIndex)
        # Change CharField to FK
        old_field = AuthorCharFieldWithIndex._meta.get_field("char_field")
        new_field = ForeignKey(Author, CASCADE, blank=True)
        new_field.set_attributes_from_name("char_field")
        with connection.schema_editor() as editor:
            editor.alter_field(
                AuthorCharFieldWithIndex, old_field, new_field, strict=True
            )
        self.assertForeignKeyExists(
            AuthorCharFieldWithIndex, "char_field_id", "schema_author"
        )