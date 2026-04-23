def test_sql_flush_allow_cascade(self):
        statements = connection.ops.sql_flush(
            no_style(),
            [Person._meta.db_table, Tag._meta.db_table],
            allow_cascade=True,
        )
        # The tables and constraints are processed in an unordered set.
        self.assertEqual(
            statements[0],
            'ALTER TABLE "BACKENDS_VERYLONGMODELNAME540F" DISABLE CONSTRAINT '
            '"BACKENDS__PERSON_ID_1DD5E829_F" KEEP INDEX;',
        )
        self.assertEqual(
            sorted(statements[1:-1]),
            [
                'TRUNCATE TABLE "BACKENDS_PERSON";',
                'TRUNCATE TABLE "BACKENDS_TAG";',
                'TRUNCATE TABLE "BACKENDS_VERYLONGMODELNAME540F";',
            ],
        )
        self.assertEqual(
            statements[-1],
            'ALTER TABLE "BACKENDS_VERYLONGMODELNAME540F" ENABLE CONSTRAINT '
            '"BACKENDS__PERSON_ID_1DD5E829_F";',
        )