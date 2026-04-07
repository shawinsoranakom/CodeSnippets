def test_references_field_by_through(self):
        operation = FieldOperation(
            "Model", "field", models.ManyToManyField("Other", through="Through")
        )
        self.assertIs(
            operation.references_field("Other", "whatever", "migrations"), True
        )
        self.assertIs(
            operation.references_field("Through", "whatever", "migrations"), True
        )
        self.assertIs(
            operation.references_field("Missing", "whatever", "migrations"), False
        )