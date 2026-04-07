def test_str(self):
        table_name = self.editor.quote_name(Person._meta.db_table)
        expected_str = "%s.%s, %s.%s DESC, (UPPER(%s.%s))" % (
            table_name,
            self.editor.quote_name("first_name"),
            table_name,
            self.editor.quote_name("last_name"),
            table_name,
            self.editor.quote_name("last_name"),
        )
        self.assertEqual(str(self.expressions), expected_str)