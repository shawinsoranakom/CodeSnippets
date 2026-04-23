def test_ops_class_include(self):
        index_name = "test_ops_class_include"
        index = Index(
            name=index_name,
            fields=["body"],
            opclasses=["text_pattern_ops"],
            include=["headline"],
        )
        with connection.schema_editor() as editor:
            editor.add_index(IndexedArticle2, index)
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query % index_name)
            self.assertCountEqual(cursor.fetchall(), [("text_pattern_ops", index_name)])