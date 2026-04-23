def test_correct_source_expressions(self):
        func = StatAggregate(x="test", y=13)
        self.assertIsInstance(func.source_expressions[0], Value)
        self.assertIsInstance(func.source_expressions[1], F)