def test_is_null_condition(self):
        with connection.schema_editor() as editor:
            index = Index(
                name="recent_article_idx",
                fields=["pub_date"],
                condition=Q(pub_date__isnull=False),
            )
            self.assertIn(
                "WHERE %s IS NOT NULL" % editor.quote_name("pub_date"),
                str(index.create_sql(Article, schema_editor=editor)),
            )
            editor.add_index(index=index, model=Article)
            with connection.cursor() as cursor:
                self.assertIn(
                    index.name,
                    connection.introspection.get_constraints(
                        cursor=cursor,
                        table_name=Article._meta.db_table,
                    ),
                )
            editor.remove_index(index=index, model=Article)