def test_rename_column_references(self):
        reference = MockReference("", {}, {("table", "column")}, {})
        statement = Statement("", reference=reference, non_reference="")
        statement.rename_column_references("table", "column", "other")
        self.assertEqual(reference.referenced_columns, {("table", "other")})