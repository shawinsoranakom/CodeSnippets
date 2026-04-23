def test_message_attrs(self):
        self.client.force_login(self.superuser)
        response = self.client.get("/auth_processor_messages/")
        self.assertContains(response, "Message 1")