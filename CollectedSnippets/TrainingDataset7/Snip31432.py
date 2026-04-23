def test_db_table(self):
        """
        Tests renaming of the table
        """

        class Author(Model):
            name = CharField(max_length=255)

            class Meta:
                app_label = "schema"

        class Book(Model):
            author = ForeignKey(Author, CASCADE)

            class Meta:
                app_label = "schema"

        # Create the table and one referring it.
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(Book)
        # Ensure the table is there to begin with
        columns = self.column_classes(Author)
        self.assertEqual(
            columns["name"][0],
            connection.features.introspected_field_types["CharField"],
        )
        # Alter the table
        with connection.schema_editor() as editor:
            editor.alter_db_table(Author, "schema_author", "schema_otherauthor")
        Author._meta.db_table = "schema_otherauthor"
        columns = self.column_classes(Author)
        self.assertEqual(
            columns["name"][0],
            connection.features.introspected_field_types["CharField"],
        )
        # Ensure the foreign key reference was updated
        self.assertForeignKeyExists(Book, "author_id", "schema_otherauthor")
        # Alter the table again
        with connection.schema_editor() as editor:
            editor.alter_db_table(Author, "schema_otherauthor", "schema_author")
        # Ensure the table is still there
        Author._meta.db_table = "schema_author"
        columns = self.column_classes(Author)
        self.assertEqual(
            columns["name"][0],
            connection.features.introspected_field_types["CharField"],
        )