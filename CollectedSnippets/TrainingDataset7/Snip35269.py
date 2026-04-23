def test_needle_msg(self):
        msg = (
            "False is not true : Couldn't find '<b>Hello</b>' in the following "
            "response\n'<p>Test</p>'"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertInHTML("<b>Hello</b>", "<p>Test</p>")