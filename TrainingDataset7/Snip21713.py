def test_invalid_source_expression(self):
        msg = "Expression 'Upper' isn't compatible with OVER clauses."
        with self.assertRaisesMessage(ValueError, msg):
            Window(expression=Upper("name"))