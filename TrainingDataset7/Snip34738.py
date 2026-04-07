def test_not_contains_with_wrong_status_code(self):
        response = self.client.get("/no_template_view/")
        msg = "Couldn't retrieve content: Response code was 200 (expected 999)"
        self.assertRaisesPrefixedMessage(
            self.assertNotContains,
            response,
            "text",
            status_code=999,
            expected_msg=msg,
        )