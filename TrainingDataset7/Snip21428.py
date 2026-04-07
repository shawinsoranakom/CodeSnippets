def test_replace_expressions_falsey(self):
        class AssignableExpression(Expression):
            def __init__(self, *source_expressions):
                super().__init__()
                self.set_source_expressions(list(source_expressions))

            def get_source_expressions(self):
                return self.source_expressions

            def set_source_expressions(self, exprs):
                self.source_expressions = exprs

        expression = AssignableExpression()
        falsey = Q()
        expression.set_source_expressions([falsey])
        replaced = expression.replace_expressions({"replacement": Expression()})
        self.assertEqual(replaced.get_source_expressions(), [falsey])