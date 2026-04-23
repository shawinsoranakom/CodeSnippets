def test_covering_ignored(self):
        index = Index(
            name="test_covering_ignored",
            fields=["headline"],
            include=["pub_date"],
        )
        with connection.schema_editor() as editor:
            editor.add_index(Article, index)
        self.assertNotIn(
            "INCLUDE (%s)" % editor.quote_name("headline"),
            str(index.create_sql(Article, editor)),
        )