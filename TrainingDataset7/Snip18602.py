def test_sql_flush(self):
        statements = connection.ops.sql_flush(
            no_style(),
            [Person._meta.db_table, Tag._meta.db_table],
        )
        # The tables and constraints are processed in an unordered set.
        self.assertEqual(
            statements[0],
            'ALTER TABLE "BACKENDS_TAG" DISABLE CONSTRAINT '
            '"BACKENDS__CONTENT_T_FD9D7A85_F" KEEP INDEX;',
        )
        self.assertEqual(
            sorted(statements[1:-1]),
            [
                'TRUNCATE TABLE "BACKENDS_PERSON";',
                'TRUNCATE TABLE "BACKENDS_TAG";',
            ],
        )
        self.assertEqual(
            statements[-1],
            'ALTER TABLE "BACKENDS_TAG" ENABLE CONSTRAINT '
            '"BACKENDS__CONTENT_T_FD9D7A85_F";',
        )