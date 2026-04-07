def test_inline_fk_db_on_delete(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(Book)
            editor.create_model(Note)
        self.assertForeignKeyNotExists(Note, "book_id", "schema_book")
        # Add a foreign key from model to the other.
        with (
            CaptureQueriesContext(connection) as ctx,
            connection.schema_editor() as editor,
        ):
            new_field = ForeignKey(Book, DB_CASCADE)
            new_field.set_attributes_from_name("book")
            editor.add_field(Note, new_field)
        self.assertForeignKeyExists(Note, "book_id", "schema_book")
        # Creating a FK field with a constraint uses a single statement without
        # a deferred ALTER TABLE.
        self.assertFalse(
            [
                sql
                for sql in (str(statement) for statement in editor.deferred_sql)
                if sql.startswith("ALTER TABLE") and "ADD CONSTRAINT" in sql
            ]
        )
        # ON DELETE clause is used.
        self.assertTrue(
            any(
                capture_query["sql"].startswith("ALTER TABLE")
                and "ON DELETE" in capture_query["sql"]
                for capture_query in ctx.captured_queries
            )
        )