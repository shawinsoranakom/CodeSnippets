def test_count_msg_prefix(self):
        msg = (
            "2 != 1 : Prefix: Found 2 instances of '<b>Hello</b>' (expected 1) in the "
            "following response\n'<b>Hello</b><b>Hello</b>'"
            ""
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertInHTML(
                "<b>Hello</b>",
                "<b>Hello</b><b>Hello</b>",
                count=1,
                msg_prefix="Prefix",
            )