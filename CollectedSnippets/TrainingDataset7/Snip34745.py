def test_missing_content_with_count(self):
        response = self.client.get("/no_template_view/")
        msg = (
            "Found 0 instances of 'thrice' (expected 3) in the following "
            f"response\n{response.content}"
        )
        self.assertRaisesPrefixedMessage(
            self.assertContains,
            response,
            "thrice",
            3,
            expected_msg=msg,
        )