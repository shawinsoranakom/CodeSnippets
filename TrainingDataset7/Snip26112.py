def test_none_body(self):
        msg = EmailMessage("subject", None, "from@example.com", ["to@example.com"])
        self.assertEqual(msg.body, "")
        # The modern email API forces trailing newlines on all text/* parts,
        # even an empty body.
        self.assertEqual(msg.message().get_payload(), "\n")