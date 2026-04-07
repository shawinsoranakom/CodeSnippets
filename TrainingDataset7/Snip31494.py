def test_alter_field_add_index_to_integerfield(self):
        # Create the table and verify no initial indexes.
        with connection.schema_editor() as editor:
            editor.create_model(Author)
        self.assertEqual(self.get_constraints_for_column(Author, "weight"), [])

        # Alter to add db_index=True and create index.
        old_field = Author._meta.get_field("weight")
        new_field = IntegerField(null=True, db_index=True)
        new_field.set_attributes_from_name("weight")
        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)
        self.assertEqual(
            self.get_constraints_for_column(Author, "weight"),
            ["schema_author_weight_587740f9"],
        )

        # Remove db_index=True to drop index.
        with connection.schema_editor() as editor:
            editor.alter_field(Author, new_field, old_field, strict=True)
        self.assertEqual(self.get_constraints_for_column(Author, "weight"), [])