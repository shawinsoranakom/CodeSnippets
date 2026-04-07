def test_rename_table_references(self):
        super().test_rename_table_references()
        self.reference.rename_table_references("to_table", "other_to_table")
        self.assertIs(self.reference.references_table("other_to_table"), True)
        self.assertIs(self.reference.references_table("to_table"), False)