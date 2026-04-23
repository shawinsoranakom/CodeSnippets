def test_partial_func_index(self):
        index_name = "partial_func_idx"
        index = Index(
            Lower("headline").desc(),
            name=index_name,
            condition=Q(pub_date__isnull=False),
        )
        with connection.schema_editor() as editor:
            editor.add_index(index=index, model=Article)
            sql = index.create_sql(Article, schema_editor=editor)
        table = Article._meta.db_table
        self.assertIs(sql.references_column(table, "headline"), True)
        sql = str(sql)
        self.assertIn("LOWER(%s)" % editor.quote_name("headline"), sql)
        self.assertIn(
            "WHERE %s IS NOT NULL" % editor.quote_name("pub_date"),
            sql,
        )
        self.assertGreater(sql.find("WHERE"), sql.find("LOWER"))
        with connection.cursor() as cursor:
            constraints = connection.introspection.get_constraints(
                cursor=cursor,
                table_name=table,
            )
        self.assertIn(index_name, constraints)
        if connection.features.supports_index_column_ordering:
            self.assertEqual(constraints[index_name]["orders"], ["DESC"])
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