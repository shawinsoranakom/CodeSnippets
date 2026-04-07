def test_covering_func_index(self):
        index_name = "covering_func_headline_idx"
        index = Index(Lower("headline"), name=index_name, include=["pub_date"])
        with connection.schema_editor() as editor:
            editor.add_index(index=index, model=Article)
            sql = index.create_sql(Article, schema_editor=editor)
        table = Article._meta.db_table
        self.assertIs(sql.references_column(table, "headline"), True)
        sql = str(sql)
        self.assertIn("LOWER(%s)" % editor.quote_name("headline"), sql)
        self.assertIn("INCLUDE (%s)" % editor.quote_name("pub_date"), sql)
        self.assertGreater(sql.find("INCLUDE"), sql.find("LOWER"))
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor=cursor,
                table_name=table,
            )
        self.assertIn(index_name, constraints)
        self.assertIn("pub_date", constraints[index_name]["columns"])
        with connection.schema_editor() as editor:
            editor.remove_index(Article, index)
        with connection.cursor() as cursor:
            self.assertNotIn(
                index_name,
                connection.introspection.get_constraints(
                    cursor=cursor,
                    table_name=table,
                ),
            )