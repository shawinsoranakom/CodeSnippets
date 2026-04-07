def test_sql_flush(self):
        self.assertEqual(
            connection.ops.sql_flush(
                no_style(),
                [Person._meta.db_table, Tag._meta.db_table],
            ),
            [
                'DELETE FROM "backends_person";',
                'DELETE FROM "backends_tag";',
            ],
        )