def test_date03(self):
        """
        #9520: Make sure |date doesn't blow up on non-dates
        """
        output = self.engine.render_to_string("date03", {"d": "fail_string"})
        self.assertEqual(output, "")