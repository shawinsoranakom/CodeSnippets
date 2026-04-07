def test_nth_null_expression(self):
        msg = "NthValue requires a non-null source expression"
        with self.assertRaisesMessage(ValueError, msg):
            NthValue(expression=None)