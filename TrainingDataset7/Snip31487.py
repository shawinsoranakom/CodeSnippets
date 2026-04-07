def test_alter_field_add_unique_to_charfield(self):
        # Create the table and verify no initial indexes.
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        self.assertEqual(self.get_constraints_for_column(Author, "name"), [])
        # Alter to add unique=True and create 2 indexes.
        old_field = Author._meta.get_field("name")
        new_field = CharField(max_length=255, unique=True)
        new_field.set_attributes_from_name("name")
        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)
        self.assertEqual(
            self.get_constraints_for_column(Author, "name"),
            ["schema_author_name_1fbc5617_like", "schema_author_name_1fbc5617_uniq"],
        )
        # Remove unique=True to drop both indexes.
        with connection.schema_editor() as editor:
            editor.alter_field(Author, new_field, old_field, strict=True)
        self.assertEqual(self.get_constraints_for_column(Author, "name"), [])