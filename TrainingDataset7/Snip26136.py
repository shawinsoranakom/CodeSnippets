def test_dummy_backend(self):
        """
        Make sure that dummy backends returns correct number of sent messages
        """
        connection = dummy.EmailBackend()
        email = EmailMessage(to=["to@example.com"])
        self.assertEqual(connection.send_messages([email, email, email]), 3)