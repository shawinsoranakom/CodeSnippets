def test_assert_not_in_html_msg_prefix(self):
        haystack = "<p>Hello</p>"
        msg = (
            "1 != 0 : Prefix: '<p>Hello</p>' unexpectedly found in the following "
            f"response\n{haystack!r}"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertNotInHTML("<p>Hello</p>", haystack=haystack, msg_prefix="Prefix")