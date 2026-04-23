def test_references_column(self):
        table = Person._meta.db_table
        self.assertIs(self.expressions.references_column(table, "first_name"), True)
        self.assertIs(self.expressions.references_column(table, "last_name"), True)
        self.assertIs(self.expressions.references_column(table, "other"), False)