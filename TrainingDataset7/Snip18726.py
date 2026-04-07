def test_sql_flush_allow_cascade(self):
        statements = connection.ops.sql_flush(
            no_style(),
            [Person._meta.db_table, Tag._meta.db_table],
            allow_cascade=True,
        )
        self.assertEqual(
            # The tables are processed in an unordered set.
            sorted(statements),
            [
                'DELETE FROM "backends_person";',
                'DELETE FROM "backends_tag";',
                'DELETE FROM "backends_verylongmodelnamezzzzzzzzzzzzzzzzzzzzzz'
                "zzzzzzzzzzzzzzzzzzzz_m2m_also_quite_long_zzzzzzzzzzzzzzzzzzzz"
                'zzzzzzzzzzzzzzzzzzzzzzz";',
            ],
        )