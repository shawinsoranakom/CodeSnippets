def test_sql_flush_allow_cascade(self):
        self.assertEqual(
            connection.ops.sql_flush(
                no_style(),
                [Person._meta.db_table, Tag._meta.db_table],
                allow_cascade=True,
            ),
            ['TRUNCATE "backends_person", "backends_tag" CASCADE;'],
        )