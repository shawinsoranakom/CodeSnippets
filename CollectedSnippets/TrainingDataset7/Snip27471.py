def test_references_field_by_name(self):
        operation = FieldOperation("MoDel", "field", models.BooleanField(default=False))
        self.assertIs(operation.references_field("model", "field", "migrations"), True)