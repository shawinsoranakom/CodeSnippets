def test_ops_class_columns_lists_sql(self):
        index = Index(
            fields=["headline"],
            name="whitespace_idx",
            opclasses=["text_pattern_ops"],
        )
        with connection.schema_editor() as editor:
            self.assertIn(
                "(%s text_pattern_ops)" % editor.quote_name("headline"),
                str(index.create_sql(Article, editor)),
            )