def test_table_names_with_views(self):
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    "CREATE VIEW introspection_article_view AS SELECT headline "
                    "from introspection_article;"
                )
            except DatabaseError as e:
                if "insufficient privileges" in str(e):
                    self.fail("The test user has no CREATE VIEW privileges")
                else:
                    raise
        try:
            self.assertIn(
                "introspection_article_view",
                connection.introspection.table_names(include_views=True),
            )
            self.assertNotIn(
                "introspection_article_view", connection.introspection.table_names()
            )
        finally:
            with connection.cursor() as cursor:
                cursor.execute("DROP VIEW introspection_article_view")