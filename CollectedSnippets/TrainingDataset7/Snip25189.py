def test_ops_class_partial(self):
        index = Index(
            name="test_ops_class_partial",
            fields=["body"],
            opclasses=["text_pattern_ops"],
            condition=Q(headline__contains="China"),
        )
        with connection.schema_editor() as editor:
            editor.add_index(IndexedArticle2, index)
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query % "test_ops_class_partial")
            self.assertCountEqual(
                cursor.fetchall(), [("text_pattern_ops", "test_ops_class_partial")]
            )