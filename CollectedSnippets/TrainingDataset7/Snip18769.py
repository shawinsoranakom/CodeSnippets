def test_rename_column_references(self):
        super().test_rename_column_references()
        self.reference.rename_column_references(
            "to_table", "second_column", "third_column"
        )
        self.assertIs(self.reference.references_column("table", "second_column"), True)
        self.assertIs(
            self.reference.references_column("to_table", "to_second_column"), True
        )
        self.reference.rename_column_references(
            "to_table", "to_first_column", "to_third_column"
        )
        self.assertIs(
            self.reference.references_column("to_table", "to_first_column"), False
        )
        self.assertIs(
            self.reference.references_column("to_table", "to_third_column"), True
        )