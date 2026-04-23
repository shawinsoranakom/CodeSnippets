def test_assertion(self):
        response = FakeResponse()
        add_message(response.wsgi_request, constants.DEBUG, "DEBUG message.")
        add_message(response.wsgi_request, constants.INFO, "INFO message.")
        add_message(response.wsgi_request, constants.SUCCESS, "SUCCESS message.")
        add_message(response.wsgi_request, constants.WARNING, "WARNING message.")
        add_message(response.wsgi_request, constants.ERROR, "ERROR message.")
        self.assertMessages(
            response,
            [
                Message(constants.DEBUG, "DEBUG message."),
                Message(constants.INFO, "INFO message."),
                Message(constants.SUCCESS, "SUCCESS message."),
                Message(constants.WARNING, "WARNING message."),
                Message(constants.ERROR, "ERROR message."),
            ],
        )