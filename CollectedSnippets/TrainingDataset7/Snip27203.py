def test_alter_id_type_with_fk(self):
        try:
            executor = MigrationExecutor(connection)
            self.assertTableNotExists("author_app_author")
            self.assertTableNotExists("book_app_book")
            # Apply initial migrations
            executor.migrate(
                [
                    ("author_app", "0001_initial"),
                    ("book_app", "0001_initial"),
                ]
            )
            self.assertTableExists("author_app_author")
            self.assertTableExists("book_app_book")
            # Rebuild the graph to reflect the new DB state
            executor.loader.build_graph()

            # Apply PK type alteration
            executor.migrate([("author_app", "0002_alter_id")])

            # Rebuild the graph to reflect the new DB state
            executor.loader.build_graph()
        finally:
            # We can't simply unapply the migrations here because there is no
            # implicit cast from VARCHAR to INT on the database level.
            with connection.schema_editor() as editor:
                editor.execute(editor.sql_delete_table % {"table": "book_app_book"})
                editor.execute(editor.sql_delete_table % {"table": "author_app_author"})
            self.assertTableNotExists("author_app_author")
            self.assertTableNotExists("book_app_book")
            executor.migrate([("author_app", None)], fake=True)