def test_not_contains_failure(self):
        response = self.client.get("/no_template_view/")
        msg = f"'once' unexpectedly found in the following response\n{response.content}"
        self.assertRaisesPrefixedMessage(
            self.assertNotContains,
            response,
            "once",
            expected_msg=msg,
        )