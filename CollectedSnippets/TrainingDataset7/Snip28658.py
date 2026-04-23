def test_db_tablespace(self):
        editor = connection.schema_editor()
        # Index with db_tablespace attribute.
        for fields in [
            # Field with db_tablespace specified on model.
            ["shortcut"],
            # Field without db_tablespace specified on model.
            ["author"],
            # Multi-column with db_tablespaces specified on model.
            ["shortcut", "isbn"],
            # Multi-column without db_tablespace specified on model.
            ["title", "author"],
        ]:
            with self.subTest(fields=fields):
                index = models.Index(fields=fields, db_tablespace="idx_tbls2")
                self.assertIn(
                    '"idx_tbls2"', str(index.create_sql(Book, editor)).lower()
                )
        # Indexes without db_tablespace attribute.
        for fields in [["author"], ["shortcut", "isbn"], ["title", "author"]]:
            with self.subTest(fields=fields):
                index = models.Index(fields=fields)
                # The DEFAULT_INDEX_TABLESPACE setting can't be tested because
                # it's evaluated when the model class is defined. As a
                # consequence, @override_settings doesn't work.
                if settings.DEFAULT_INDEX_TABLESPACE:
                    self.assertIn(
                        '"%s"' % settings.DEFAULT_INDEX_TABLESPACE,
                        str(index.create_sql(Book, editor)).lower(),
                    )
                else:
                    self.assertNotIn("TABLESPACE", str(index.create_sql(Book, editor)))
        # Field with db_tablespace specified on the model and an index without
        # db_tablespace.
        index = models.Index(fields=["shortcut"])
        self.assertIn('"idx_tbls"', str(index.create_sql(Book, editor)).lower())