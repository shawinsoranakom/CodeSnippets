def test_msg_prefix(self):
        msg = (
            "False is not true : Prefix: Couldn't find '<b>Hello</b>' in the following "
            'response\n\'<input type="text" name="Hello" />\''
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertInHTML(
                "<b>Hello</b>",
                '<input type="text" name="Hello" />',
                msg_prefix="Prefix",
            )