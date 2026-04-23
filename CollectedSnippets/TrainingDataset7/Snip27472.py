def test_references_field_by_remote_field_model(self):
        operation = FieldOperation(
            "Model", "field", models.ForeignKey("Other", models.CASCADE)
        )
        self.assertIs(
            operation.references_field("Other", "whatever", "migrations"), True
        )
        self.assertIs(
            operation.references_field("Missing", "whatever", "migrations"), False
        )