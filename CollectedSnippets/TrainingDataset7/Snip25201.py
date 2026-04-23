def test_multiple_conditions(self):
        with connection.schema_editor() as editor:
            index = Index(
                name="recent_article_idx",
                fields=["pub_date", "headline"],
                condition=(
                    Q(
                        pub_date__gt=datetime.datetime(
                            year=2015,
                            month=1,
                            day=1,
                            tzinfo=timezone.get_current_timezone(),
                        )
                    )
                    & Q(headline__contains="China")
                ),
            )
            sql = str(index.create_sql(Article, schema_editor=editor))
            where = sql.find("WHERE")
            self.assertIn("WHERE (%s" % editor.quote_name("pub_date"), sql)
            # Because each backend has different syntax for the operators,
            # check ONLY the occurrence of headline in the SQL.
            self.assertGreater(sql.rfind("headline"), where)
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