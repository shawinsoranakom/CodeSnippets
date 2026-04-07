def test_func_with_tablespace(self):
        # Functional index with db_tablespace attribute.
        index = models.Index(
            Lower("shortcut").desc(),
            name="functional_tbls",
            db_tablespace="idx_tbls2",
        )
        with connection.schema_editor() as editor:
            sql = str(index.create_sql(Book, editor))
            self.assertIn(editor.quote_name("idx_tbls2"), sql)
        # Functional index without db_tablespace attribute.
        index = models.Index(Lower("shortcut").desc(), name="functional_no_tbls")
        with connection.schema_editor() as editor:
            sql = str(index.create_sql(Book, editor))
            # The DEFAULT_INDEX_TABLESPACE setting can't be tested because it's
            # evaluated when the model class is defined. As a consequence,
            # @override_settings doesn't work.
            if settings.DEFAULT_INDEX_TABLESPACE:
                self.assertIn(
                    editor.quote_name(settings.DEFAULT_INDEX_TABLESPACE),
                    sql,
                )
            else:
                self.assertNotIn("TABLESPACE", sql)