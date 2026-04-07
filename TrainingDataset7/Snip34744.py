def test_missing_content(self):
        response = self.client.get("/no_template_view/")
        msg = f"Couldn't find 'thrice' in the following response\n{response.content}"
        self.assertRaisesPrefixedMessage(
            self.assertContains,
            response,
            "thrice",
            expected_msg=msg,
            msg_prefix="Custom prexix",
        )