def test_ops_class_partial_tablespace(self):
        indexname = "test_ops_class_tblspace"
        index = Index(
            name=indexname,
            fields=["body"],
            opclasses=["text_pattern_ops"],
            condition=Q(headline__contains="China"),
            db_tablespace="pg_default",
        )
        with connection.schema_editor() as editor:
            editor.add_index(IndexedArticle2, index)
            self.assertIn(
                'TABLESPACE "pg_default" ',
                str(index.create_sql(IndexedArticle2, editor)),
            )
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query % indexname)
            self.assertCountEqual(cursor.fetchall(), [("text_pattern_ops", indexname)])