def test_long_content(self):
        long_content = (
            b"This is a very very very very very very very very long message which "
            b"exceeds the max limit of truncation."
        )
        response = HttpResponse(long_content)
        msg = f"Couldn't find 'thrice' in the following response\n{long_content}"
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertContains(response, "thrice")

        msg = (
            "Found 1 instances of 'This' (expected 3) in the following response\n"
            f"{long_content}"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertContains(response, "This", 3)

        msg = f"'very' unexpectedly found in the following response\n{long_content}"
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertNotContains(response, "very")