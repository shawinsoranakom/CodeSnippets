def test_reference_field_by_through_fields(self):
        operation = FieldOperation(
            "Model",
            "field",
            models.ManyToManyField(
                "Other", through="Through", through_fields=("first", "second")
            ),
        )
        self.assertIs(
            operation.references_field("Other", "whatever", "migrations"), True
        )
        self.assertIs(
            operation.references_field("Through", "whatever", "migrations"), False
        )
        self.assertIs(
            operation.references_field("Through", "first", "migrations"), True
        )
        self.assertIs(
            operation.references_field("Through", "second", "migrations"), True
        )