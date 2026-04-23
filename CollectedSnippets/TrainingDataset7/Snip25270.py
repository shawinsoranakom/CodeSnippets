def test_sequence_list(self):
        sequences = connection.introspection.sequence_list()
        reporter_seqs = [
            seq for seq in sequences if seq["table"] == Reporter._meta.db_table
        ]
        self.assertEqual(
            len(reporter_seqs), 1, "Reporter sequence not found in sequence_list()"
        )
        self.assertEqual(reporter_seqs[0]["column"], "id")