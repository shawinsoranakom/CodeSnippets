def test_mismatching_length(self):
        response = FakeResponse()
        add_message(response.wsgi_request, constants.INFO, "INFO message.")
        msg = (
            "Lists differ: [Message(level=20, message='INFO message.')] != []\n\n"
            "First list contains 1 additional elements.\n"
            "First extra element 0:\n"
            "Message(level=20, message='INFO message.')\n\n"
            "- [Message(level=20, message='INFO message.')]\n"
            "+ []"
        )
        with self.assertRaisesMessage(AssertionError, msg):
            self.assertMessages(response, [])