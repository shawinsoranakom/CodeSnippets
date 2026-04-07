def test_ordered(self):
        response = FakeResponse()
        add_message(response.wsgi_request, constants.INFO, "First message.")
        add_message(response.wsgi_request, constants.WARNING, "Second message.")
        expected_messages = [
            Message(constants.WARNING, "Second message."),
            Message(constants.INFO, "First message."),
        ]
        self.assertMessages(response, expected_messages, ordered=False)
        with self.assertRaisesMessage(AssertionError, "Lists differ: "):
            self.assertMessages(response, expected_messages)