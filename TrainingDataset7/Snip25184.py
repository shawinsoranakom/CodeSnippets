def test_condition_ignored(self):
        index = Index(
            name="test_condition_ignored",
            fields=["published"],
            condition=Q(published=True),
        )
        with connection.schema_editor() as editor:
            # This would error if condition weren't ignored.
            editor.add_index(Article, index)

        self.assertNotIn(
            "WHERE %s" % editor.quote_name("published"),
            str(index.create_sql(Article, editor)),
        )