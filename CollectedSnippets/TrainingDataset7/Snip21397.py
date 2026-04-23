def test_pickle_expression(self):
        expr = Value(1)
        expr.convert_value  # populate cached property
        self.assertEqual(pickle.loads(pickle.dumps(expr)), expr)