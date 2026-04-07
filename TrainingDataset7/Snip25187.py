def test_ops_class(self):
        index = Index(
            name="test_ops_class",
            fields=["headline"],
            opclasses=["varchar_pattern_ops"],
        )
        with connection.schema_editor() as editor:
            editor.add_index(IndexedArticle2, index)
        with editor.connection.cursor() as cursor:
            cursor.execute(self.get_opclass_query % "test_ops_class")
            self.assertEqual(
                cursor.fetchall(), [("varchar_pattern_ops", "test_ops_class")]
            )