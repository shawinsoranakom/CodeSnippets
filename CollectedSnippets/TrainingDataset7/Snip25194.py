def test_ops_class_include_tablespace(self):
        index_name = "test_ops_class_include_tblspace"
        index = Index(
            name=index_name,
            fields=["body"],
            opclasses=["text_pattern_ops"],
            include=["headline"],
            db_tablespace="pg_default",
        )
        with connection.schema_editor() as editor:
            editor.add_index(IndexedArticle2, index)
            self.assertIn(
                'TABLESPACE "pg_default"',
                str(index.create_sql(IndexedArticle2, editor)),
            )
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query % index_name)
            self.assertCountEqual(cursor.fetchall(), [("text_pattern_ops", index_name)])