def test_references_table(self):
        statement = Statement(
            "", reference=MockReference("", {"table"}, {}, {}), non_reference=""
        )
        self.assertIs(statement.references_table("table"), True)
        self.assertIs(statement.references_table("other"), False)