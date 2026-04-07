def test_sql_flush_sequences(self):
        # allow_cascade doesn't change statements on MySQL.
        for allow_cascade in [False, True]:
            with self.subTest(allow_cascade=allow_cascade):
                self.assertEqual(
                    connection.ops.sql_flush(
                        no_style(),
                        [Person._meta.db_table, Tag._meta.db_table],
                        reset_sequences=True,
                        allow_cascade=allow_cascade,
                    ),
                    [
                        "SET FOREIGN_KEY_CHECKS = 0;",
                        "TRUNCATE `backends_person`;",
                        "TRUNCATE `backends_tag`;",
                        "SET FOREIGN_KEY_CHECKS = 1;",
                    ],
                )