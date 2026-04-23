def test_references_table(self):
        super().test_references_table()
        self.assertIs(self.reference.references_table("to_table"), True)