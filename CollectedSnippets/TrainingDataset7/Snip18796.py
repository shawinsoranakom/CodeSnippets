def test_split_identifier(self):
        self.assertEqual(split_identifier("some_table"), ("", "some_table"))
        self.assertEqual(split_identifier('"some_table"'), ("", "some_table"))
        self.assertEqual(
            split_identifier('namespace"."some_table'), ("namespace", "some_table")
        )
        self.assertEqual(
            split_identifier('"namespace"."some_table"'), ("namespace", "some_table")
        )