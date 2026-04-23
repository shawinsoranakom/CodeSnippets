def test_custom_backend(self):
        """Test custom backend defined in this suite."""
        conn = mail.get_connection("mail.custombackend.EmailBackend")
        self.assertTrue(hasattr(conn, "test_outbox"))
        email = EmailMessage(to=["to@example.com"])
        conn.send_messages([email])
        self.assertEqual(len(conn.test_outbox), 1)