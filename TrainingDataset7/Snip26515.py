def test_custom_levelname(self):
        response = FakeResponse()
        add_message(response.wsgi_request, 42, "CUSTOM message.")
        self.assertMessages(response, [Message(42, "CUSTOM message.")])