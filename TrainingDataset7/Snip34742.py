def test_insufficient_count(self):
        response = self.client.get("/no_template_view/")
        msg = (
            "Found 1 instances of 'once' (expected 2) in the following response\n"
            f"{response.content}"
        )
        self.assertRaisesPrefixedMessage(
            self.assertContains,
            response,
            "once",
            2,
            expected_msg=msg,
        )