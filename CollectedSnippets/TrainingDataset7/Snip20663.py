def test_nth_negative_nth_value(self):
        msg = "NthValue requires a positive integer as for nth"
        with self.assertRaisesMessage(ValueError, msg):
            NthValue(expression="salary", nth=-1)