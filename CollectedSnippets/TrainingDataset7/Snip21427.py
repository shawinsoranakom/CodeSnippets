def test_get_expression_for_validation_only_one_source_expression(self):
        expression = Expression()
        expression.constraint_validation_compatible = False
        msg = (
            "Expressions with constraint_validation_compatible set to False must have "
            "only one source expression."
        )
        with self.assertRaisesMessage(ValueError, msg):
            expression.get_expression_for_validation()