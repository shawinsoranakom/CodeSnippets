def test_unexpected_presence(self):
        response = self.client.get("/no_template_view/")
        msg = (
            "Found 1 instances of 'once' (expected 0) in the following "
            f"response\n{response.content}"
        )
        self.assertRaisesPrefixedMessage(
            self.assertContains,
            response,
            "once",
            count=0,
            expected_msg=msg,
        )