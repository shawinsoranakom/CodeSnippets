def test_references_column(self):
        super().test_references_column()
        self.assertIs(
            self.reference.references_column("to_table", "second_column"), False
        )
        self.assertIs(
            self.reference.references_column("to_table", "to_second_column"), True
        )