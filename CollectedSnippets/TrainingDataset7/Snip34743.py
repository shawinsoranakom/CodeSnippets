def test_excessive_count(self):
        response = self.client.get("/no_template_view/")
        msg = (
            "Found 2 instances of 'twice' (expected 1) in the following response\n"
            f"{response.content}"
        )
        self.assertRaisesPrefixedMessage(
            self.assertContains,
            response,
            "twice",
            count=1,
            expected_msg=msg,
        )