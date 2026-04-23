def test_deconstruct_boolean_expression(self):
        expr = RawSQL("1 = 1", BooleanField())
        q = Q(expr)
        _, args, kwargs = q.deconstruct()
        self.assertEqual(args, (expr,))
        self.assertEqual(kwargs, {})