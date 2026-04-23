def test_validate_expression_generated_field_stored(self):
        self.assertGeneratedFieldWithExpressionIsValidated(
            model=GeneratedFieldStoredProduct
        )