def test_create_index_ignores_opclasses(self):
        index = Index(
            name="test_ops_class",
            fields=["headline"],
            opclasses=["varchar_pattern_ops"],
        )
        with connection.schema_editor() as editor:
            # This would error if opclasses weren't ignored.
            editor.add_index(IndexedArticle2, index)