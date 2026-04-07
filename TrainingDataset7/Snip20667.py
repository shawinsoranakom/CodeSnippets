def test_null_source_lead(self):
        msg = "Lead requires a non-null source expression"
        with self.assertRaisesMessage(ValueError, msg):
            Lead(expression=None)