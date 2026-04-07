def test_lead_negative_offset(self):
        msg = "Lead requires a positive integer for the offset"
        with self.assertRaisesMessage(ValueError, msg):
            Lead(expression="salary", offset=-1)