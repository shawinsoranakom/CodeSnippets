def test_references_field_by_generated_field(self):
        operation = FieldOperation(
            "Model",
            "field",
            models.GeneratedField(
                expression=F("foo") + F("bar"),
                output_field=models.IntegerField(),
                db_persist=True,
            ),
        )
        self.assertIs(operation.references_field("Model", "foo", "migrations"), True)
        self.assertIs(operation.references_field("Model", "bar", "migrations"), True)
        self.assertIs(operation.references_field("Model", "alien", "migrations"), False)
        self.assertIs(operation.references_field("Other", "foo", "migrations"), False)