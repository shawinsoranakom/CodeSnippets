def test_sql_flush_sequences_allow_cascade(self):
        statements = connection.ops.sql_flush(
            no_style(),
            [Person._meta.db_table, Tag._meta.db_table],
            reset_sequences=True,
            allow_cascade=True,
        )
        # The tables and constraints are processed in an unordered set.
        self.assertEqual(
            statements[0],
            'ALTER TABLE "BACKENDS_VERYLONGMODELNAME540F" DISABLE CONSTRAINT '
            '"BACKENDS__PERSON_ID_1DD5E829_F" KEEP INDEX;',
        )
        self.assertEqual(
            sorted(statements[1:4]),
            [
                'TRUNCATE TABLE "BACKENDS_PERSON";',
                'TRUNCATE TABLE "BACKENDS_TAG";',
                'TRUNCATE TABLE "BACKENDS_VERYLONGMODELNAME540F";',
            ],
        )
        self.assertEqual(
            statements[4],
            'ALTER TABLE "BACKENDS_VERYLONGMODELNAME540F" ENABLE CONSTRAINT '
            '"BACKENDS__PERSON_ID_1DD5E829_F";',
        )
        # Sequences.
        self.assertEqual(len(statements[5:]), 3)
        self.assertIn("BACKENDS_PERSON_SQ", statements[5])
        self.assertIn("BACKENDS_VERYLONGMODELN7BE2_SQ", statements[6])
        self.assertIn("BACKENDS_TAG_SQ", statements[7])