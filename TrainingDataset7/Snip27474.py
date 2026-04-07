def test_references_field_by_to_fields(self):
        operation = FieldOperation(
            "Model",
            "field",
            models.ForeignKey("Other", models.CASCADE, to_field="field"),
        )
        self.assertIs(operation.references_field("Other", "field", "migrations"), True)
        self.assertIs(
            operation.references_field("Other", "whatever", "migrations"), False
        )
        self.assertIs(
            operation.references_field("Missing", "whatever", "migrations"), False
        )