def test_ops_class_descending(self):
        indexname = "test_ops_class_ordered"
        index = Index(
            name=indexname,
            fields=["-body"],
            opclasses=["text_pattern_ops"],
        )
        with connection.schema_editor() as editor:
            editor.add_index(IndexedArticle2, index)
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query % indexname)
            self.assertCountEqual(cursor.fetchall(), [("text_pattern_ops", indexname)])