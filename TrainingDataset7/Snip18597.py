def test_get_sequences(self):
        with connection.cursor() as cursor:
            seqs = connection.introspection.get_sequences(
                cursor, Square._meta.db_table, Square._meta.local_fields
            )
            self.assertEqual(len(seqs), 1)
            self.assertIsNotNone(seqs[0]["name"])
            self.assertEqual(seqs[0]["table"], Square._meta.db_table)
            self.assertEqual(seqs[0]["column"], "id")