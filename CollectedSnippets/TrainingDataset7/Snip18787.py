def test_references_table(self):
        self.assertIs(self.expressions.references_table(Person._meta.db_table), True)
        self.assertIs(self.expressions.references_table("other"), False)