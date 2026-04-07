def test_boolean_expression(self):
        q = Q(ExpressionWrapper(Q(price__gt=20), output_field=BooleanField()))
        self.assertIs(q.check({"price": 25}), True)
        self.assertIs(q.check({"price": Value(10)}), False)