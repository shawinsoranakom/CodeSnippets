def test_cc(self):
        """Regression test for #7722"""
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com"],
            cc=["cc@example.com"],
        )
        message = email.message()
        self.assertEqual(message["Cc"], "cc@example.com")
        self.assertEqual(email.recipients(), ["to@example.com", "cc@example.com"])

        # Test multiple CC with multiple To
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com", "other@example.com"],
            cc=["cc@example.com", "cc.other@example.com"],
        )
        message = email.message()
        self.assertEqual(message["Cc"], "cc@example.com, cc.other@example.com")
        self.assertEqual(
            email.recipients(),
            [
                "to@example.com",
                "other@example.com",
                "cc@example.com",
                "cc.other@example.com",
            ],
        )

        # Testing with Bcc
        email = EmailMessage(
            "Subject",
            "Content",
            "from@example.com",
            ["to@example.com", "other@example.com"],
            cc=["cc@example.com", "cc.other@example.com"],
            bcc=["bcc@example.com"],
        )
        message = email.message()
        self.assertEqual(message["Cc"], "cc@example.com, cc.other@example.com")
        self.assertEqual(
            email.recipients(),
            [
                "to@example.com",
                "other@example.com",
                "cc@example.com",
                "cc.other@example.com",
                "bcc@example.com",
            ],
        )