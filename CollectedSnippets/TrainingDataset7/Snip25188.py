def test_ops_class_multiple_columns(self):
        index = Index(
            name="test_ops_class_multiple",
            fields=["headline", "body"],
            opclasses=["varchar_pattern_ops", "text_pattern_ops"],
        )
        with connection.schema_editor() as editor:
            editor.add_index(IndexedArticle2, index)
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query % "test_ops_class_multiple")
            expected_ops_classes = (
                ("varchar_pattern_ops", "test_ops_class_multiple"),
                ("text_pattern_ops", "test_ops_class_multiple"),
            )
            self.assertCountEqual(cursor.fetchall(), expected_ops_classes)