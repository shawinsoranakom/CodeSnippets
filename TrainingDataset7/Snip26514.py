def test_with_tags(self):
        response = FakeResponse()
        add_message(
            response.wsgi_request,
            constants.INFO,
            "INFO message.",
            extra_tags="extra-info",
        )
        add_message(
            response.wsgi_request,
            constants.SUCCESS,
            "SUCCESS message.",
            extra_tags="extra-success",
        )
        add_message(
            response.wsgi_request,
            constants.WARNING,
            "WARNING message.",
            extra_tags="extra-warning",
        )
        add_message(
            response.wsgi_request,
            constants.ERROR,
            "ERROR message.",
            extra_tags="extra-error",
        )
        self.assertMessages(
            response,
            [
                Message(constants.INFO, "INFO message.", "extra-info"),
                Message(constants.SUCCESS, "SUCCESS message.", "extra-success"),
                Message(constants.WARNING, "WARNING message.", "extra-warning"),
                Message(constants.ERROR, "ERROR message.", "extra-error"),
            ],
        )