def test_references_index(self):
        statement = Statement(
            "",
            reference=MockReference("", {}, {}, {("table", "index")}),
            non_reference="",
        )
        self.assertIs(statement.references_index("table", "index"), True)
        self.assertIs(statement.references_index("other", "index"), False)