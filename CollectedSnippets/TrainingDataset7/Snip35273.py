def test_long_haystack(self):
        haystack = (
            "<p>This is a very very very very very very very very long message which "
            "exceeds the max limit of truncation.</p>"
        )
        msg = f"Couldn't find '<b>Hello</b>' in the following response\n{haystack!r}"
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertInHTML("<b>Hello</b>", haystack)

        msg = (
            "Found 0 instances of '<b>This</b>' (expected 3) in the following response"
            f"\n{haystack!r}"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertInHTML("<b>This</b>", haystack, 3)