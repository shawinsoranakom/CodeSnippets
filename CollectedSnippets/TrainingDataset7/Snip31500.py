def test_rename_table_renames_deferred_sql_references(self):
        with connection.schema_editor() as editor:
            editor.create_model(Author)
            editor.create_model(Book)
            editor.alter_db_table(Author, "schema_author", "schema_renamed_author")
            editor.alter_db_table(Author, "schema_book", "schema_renamed_book")
            try:
                self.assertGreater(len(editor.deferred_sql), 0)
                for statement in editor.deferred_sql:
                    self.assertIs(statement.references_table("schema_author"), False)
                    self.assertIs(statement.references_table("schema_book"), False)
            finally:
                editor.alter_db_table(Author, "schema_renamed_author", "schema_author")
                editor.alter_db_table(Author, "schema_renamed_book", "schema_book")