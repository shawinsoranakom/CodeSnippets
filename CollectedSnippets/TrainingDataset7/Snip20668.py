def test_null_source_lag(self):
        msg = "Lag requires a non-null source expression"
        with self.assertRaisesMessage(ValueError, msg):
            Lag(expression=None)