def test_rename_table_references(self):
        reference = MockReference("", {"table"}, {}, {})
        statement = Statement("", reference=reference, non_reference="")
        statement.rename_table_references("table", "other")
        self.assertEqual(reference.referenced_tables, {"other"})