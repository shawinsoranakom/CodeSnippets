def test_partial_index(self):
        with connection.schema_editor() as editor:
            index = Index(
                name="recent_article_idx",
                fields=["pub_date"],
                condition=Q(
                    pub_date__gt=datetime.datetime(
                        year=2015,
                        month=1,
                        day=1,
                        # PostgreSQL would otherwise complain about the lookup
                        # being converted to a mutable function (by removing
                        # the timezone in the cast) which is forbidden.
                        tzinfo=timezone.get_current_timezone(),
                    ),
                ),
            )
            self.assertIn(
                "WHERE %s" % editor.quote_name("pub_date"),
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