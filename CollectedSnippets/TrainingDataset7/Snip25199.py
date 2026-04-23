def test_integer_restriction_partial(self):
        with connection.schema_editor() as editor:
            index = Index(
                name="recent_article_idx",
                fields=["id"],
                condition=Q(pk__gt=1),
            )
            self.assertIn(
                "WHERE %s" % editor.quote_name("id"),
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