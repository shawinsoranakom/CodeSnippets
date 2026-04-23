def test_middleware_disabled(self):
        """
        When the middleware is disabled, an exception is raised when one
        attempts to store a message.
        """
        data = {
            "messages": ["Test message %d" % x for x in range(5)],
        }
        reverse("show_message")
        for level in ("debug", "info", "success", "warning", "error"):
            add_url = reverse("add_message", args=(level,))
            with self.assertRaises(MessageFailure):
                self.client.post(add_url, data, follow=True)