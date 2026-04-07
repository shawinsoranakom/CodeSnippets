def test_send_messages_zero_sent(self):
        """A message isn't sent if it doesn't have any recipients."""
        backend = smtp.EmailBackend()
        backend.connection = mock.Mock(spec=object())
        email = EmailMessage("Subject", "Content", "from@example.com", to=[])
        sent = backend.send_messages([email])
        self.assertEqual(sent, 0)