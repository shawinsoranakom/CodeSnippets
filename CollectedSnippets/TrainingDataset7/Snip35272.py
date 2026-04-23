def test_base(self):
        haystack = "<p><b>Hello</b> <span>there</span>! Hi <span>there</span>!</p>"

        self.assertInHTML("<b>Hello</b>", haystack=haystack)
        msg = f"Couldn't find '<p>Howdy</p>' in the following response\n{haystack!r}"
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertInHTML("<p>Howdy</p>", haystack)

        self.assertInHTML("<span>there</span>", haystack=haystack, count=2)
        msg = (
            "Found 1 instances of '<b>Hello</b>' (expected 2) in the following response"
            f"\n{haystack!r}"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertInHTML("<b>Hello</b>", haystack=haystack, count=2)