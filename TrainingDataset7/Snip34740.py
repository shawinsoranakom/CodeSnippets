def test_count_mismatch(self):
        response = self.client.get("/no_template_view/")
        msg = (
            "Found 0 instances of 'never' (expected 1) in the following response\n"
            f"{response.content}"
        )
        self.assertRaisesPrefixedMessage(
            self.assertContains,
            response,
            "never",
            count=1,
            expected_msg=msg,
        )