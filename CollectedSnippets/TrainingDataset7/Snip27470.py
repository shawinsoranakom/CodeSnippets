def test_references_model(self):
        operation = FieldOperation(
            "MoDel", "field", models.ForeignKey("Other", models.CASCADE)
        )
        # Model name match.
        self.assertIs(operation.references_model("mOdEl", "migrations"), True)
        # Referenced field.
        self.assertIs(operation.references_model("oTher", "migrations"), True)
        # Doesn't reference.
        self.assertIs(operation.references_model("Whatever", "migrations"), False)