def test_alter_field_db_collation(self):
        collation = connection.features.test_collations.get("non_default")
        if not collation:
            self.skipTest("Language collations are not supported.")

        with connection.schema_editor() as editor:
            editor.create_model(Author)

        old_field = Author._meta.get_field("name")
        new_field = CharField(max_length=255, db_collation=collation)
        new_field.set_attributes_from_name("name")
        new_field.model = Author
        with connection.schema_editor() as editor:
            editor.alter_field(Author, old_field, new_field, strict=True)
        self.assertEqual(
            self.get_column_collation(Author._meta.db_table, "name"),
            collation,
        )
        with connection.schema_editor() as editor:
            editor.alter_field(Author, new_field, old_field, strict=True)
        self.assertIsNone(self.get_column_collation(Author._meta.db_table, "name"))