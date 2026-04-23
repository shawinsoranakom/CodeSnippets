def test_validate_multiline_headers(self):
        # Ticket #18861 - Validate emails when using the locmem backend
        with self.assertRaises(ValueError):
            send_mail(
                "Subject\nMultiline", "Content", "from@example.com", ["to@example.com"]
            )