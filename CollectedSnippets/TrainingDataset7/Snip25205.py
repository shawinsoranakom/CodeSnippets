def test_covering_partial_index(self):
        index = Index(
            name="covering_partial_headline_idx",
            fields=["headline"],
            include=["pub_date"],
            condition=Q(pub_date__isnull=False),
        )
        with connection.schema_editor() as editor:
            extra_sql = ""
            if settings.DEFAULT_INDEX_TABLESPACE:
                extra_sql = "TABLESPACE %s " % editor.quote_name(
                    settings.DEFAULT_INDEX_TABLESPACE
                )
            self.assertIn(
                "(%s) INCLUDE (%s) %sWHERE %s "
                % (
                    editor.quote_name("headline"),
                    editor.quote_name("pub_date"),
                    extra_sql,
                    editor.quote_name("pub_date"),
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
                    ["headline", "pub_date"],
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