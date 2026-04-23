def test_validate_expression_generated_field_virtual(self):
        self.assertGeneratedFieldWithExpressionIsValidated(
            model=GeneratedFieldVirtualProduct
        )