def test_fk_alter_on_delete(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(Book)
        self.assertForeignKeyExists(Book, "author_id", "schema_author")
        # Change CASCADE to DB_CASCADE.
        old_field = Book._meta.get_field("author")
        new_field = ForeignKey(Author, DB_CASCADE)
        new_field.set_attributes_from_name("author")
        with (
            connection.schema_editor() as editor,
            CaptureQueriesContext(connection) as ctx,
        ):
            editor.alter_field(Book, old_field, new_field)
        self.assertForeignKeyExists(Book, "author_id", "schema_author")
        self.assertIs(
            any("ON DELETE" in query["sql"] for query in ctx.captured_queries), True
        )
        # Change DB_CASCADE to CASCADE.
        old_field = new_field
        new_field = ForeignKey(Author, CASCADE)
        new_field.set_attributes_from_name("author")
        with (
            connection.schema_editor() as editor,
            CaptureQueriesContext(connection) as ctx,
        ):
            editor.alter_field(Book, old_field, new_field)
        self.assertForeignKeyExists(Book, "author_id", "schema_author")
        self.assertIs(
            any("ON DELETE" in query["sql"] for query in ctx.captured_queries), False
        )