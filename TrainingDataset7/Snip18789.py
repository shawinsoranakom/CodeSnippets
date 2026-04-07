def test_rename_table_references(self):
        table = Person._meta.db_table
        self.expressions.rename_table_references(table, "other")
        self.assertIs(self.expressions.references_table(table), False)
        self.assertIs(self.expressions.references_table("other"), True)
        self.assertIn(
            "%s.%s"
            % (
                self.editor.quote_name("other"),
                self.editor.quote_name("first_name"),
            ),
            str(self.expressions),
        )