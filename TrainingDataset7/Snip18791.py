def test_rename_column_references(self):
        table = Person._meta.db_table
        self.expressions.rename_column_references(table, "first_name", "other")
        self.assertIs(self.expressions.references_column(table, "other"), True)
        self.assertIs(self.expressions.references_column(table, "first_name"), False)
        self.assertIn(
            "%s.%s" % (self.editor.quote_name(table), self.editor.quote_name("other")),
            str(self.expressions),
        )