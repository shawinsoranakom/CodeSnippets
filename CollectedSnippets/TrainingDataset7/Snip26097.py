def test_to_header(self):
        """
        Make sure we can manually set the To header (#17444)
        """
        email = EmailMessage(
            to=["list-subscriber@example.com", "list-subscriber2@example.com"],
            headers={"To": "mailing-list@example.com"},
        )
        message = email.message()
        self.assertEqual(message.get_all("To"), ["mailing-list@example.com"])
        self.assertEqual(
            email.to, ["list-subscriber@example.com", "list-subscriber2@example.com"]
        )

        # If we don't set the To header manually, it should default to the `to`
        # argument to the constructor.
        email = EmailMessage(
            to=["list-subscriber@example.com", "list-subscriber2@example.com"],
        )
        message = email.message()
        self.assertEqual(
            message.get_all("To"),
            ["list-subscriber@example.com, list-subscriber2@example.com"],
        )
        self.assertEqual(
            email.to, ["list-subscriber@example.com", "list-subscriber2@example.com"]
        )