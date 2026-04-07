def test_covering_index(self):
        index = Index(
            name="covering_headline_idx",
            fields=["headline"],
            include=["pub_date", "published"],
        )
        with connection.schema_editor() as editor:
            self.assertIn(
                "(%s) INCLUDE (%s, %s)"
                % (
                    editor.quote_name("headline"),
                    editor.quote_name("pub_date"),
                    editor.quote_name("published"),
                ),
                str(index.create_sql(Article, editor)),
            )
            editor.add_index(Article, index)
            with connection.cursor() as cursor:
                constraints = connection.introspection.get_constraints(
                    cursor=cursor,
                    table_name=Article._meta.db_table,
                )
                self.assertIn(index.name, constraints)
                self.assertEqual(
                    constraints[index.name]["columns"],
                    ["headline", "pub_date", "published"],
                )
            editor.remove_index(Article, index)
            with connection.cursor() as cursor:
                self.assertNotIn(
                    index.name,
                    connection.introspection.get_constraints(
                        cursor=cursor,
                        table_name=Article._meta.db_table,
                    ),
                )