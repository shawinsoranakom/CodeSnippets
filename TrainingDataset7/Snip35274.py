def test_assert_not_in_html(self):
        haystack = "<p><b>Hello</b> <span>there</span>! Hi <span>there</span>!</p>"
        self.assertNotInHTML("<b>Hi</b>", haystack=haystack)
        msg = (
            "'<b>Hello</b>' unexpectedly found in the following response"
            f"\n{haystack!r}"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertNotInHTML("<b>Hello</b>", haystack=haystack)