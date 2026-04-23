def test_header_omitted_for_no_to_recipients(self):
        message = EmailMessage(
            "Subject", "Content", "from@example.com", cc=["cc@example.com"]
        ).message()
        self.assertNotIn("To", message)