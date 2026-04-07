def test_references_column(self):
        self.assertIs(self.reference.references_column("other", "first_column"), False)
        self.assertIs(self.reference.references_column("table", "third_column"), False)
        self.assertIs(self.reference.references_column("table", "first_column"), True)