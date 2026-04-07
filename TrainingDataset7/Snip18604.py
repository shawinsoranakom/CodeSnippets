def test_sql_flush_sequences(self):
        statements = connection.ops.sql_flush(
            no_style(),
            [Person._meta.db_table, Tag._meta.db_table],
            reset_sequences=True,
        )
        # The tables and constraints are processed in an unordered set.
        self.assertEqual(
            statements[0],
            'ALTER TABLE "BACKENDS_TAG" DISABLE CONSTRAINT '
            '"BACKENDS__CONTENT_T_FD9D7A85_F" KEEP INDEX;',
        )
        self.assertEqual(
            sorted(statements[1:3]),
            [
                'TRUNCATE TABLE "BACKENDS_PERSON";',
                'TRUNCATE TABLE "BACKENDS_TAG";',
            ],
        )
        self.assertEqual(
            statements[3],
            'ALTER TABLE "BACKENDS_TAG" ENABLE CONSTRAINT '
            '"BACKENDS__CONTENT_T_FD9D7A85_F";',
        )
        # Sequences.
        self.assertEqual(len(statements[4:]), 2)
        self.assertIn("BACKENDS_PERSON_SQ", statements[4])
        self.assertIn("BACKENDS_TAG_SQ", statements[5])