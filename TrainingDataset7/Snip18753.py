def test_references_table(self):
        self.assertIs(self.reference.references_table("table"), True)
        self.assertIs(self.reference.references_table("other"), False)