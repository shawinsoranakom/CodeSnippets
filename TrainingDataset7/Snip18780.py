def test_references_column(self):
        statement = Statement(
            "",
            reference=MockReference("", {}, {("table", "column")}, {}),
            non_reference="",
        )
        self.assertIs(statement.references_column("table", "column"), True)
        self.assertIs(statement.references_column("other", "column"), False)