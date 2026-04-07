def test_references_field_by_from_fields(self):
        operation = FieldOperation(
            "Model",
            "field",
            models.fields.related.ForeignObject(
                "Other", models.CASCADE, ["from"], ["to"]
            ),
        )
        self.assertIs(operation.references_field("Model", "from", "migrations"), True)
        self.assertIs(operation.references_field("Model", "to", "migrations"), False)
        self.assertIs(operation.references_field("Other", "from", "migrations"), False)
        self.assertIs(operation.references_field("Model", "to", "migrations"), False)