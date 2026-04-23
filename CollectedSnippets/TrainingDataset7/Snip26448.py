def test_middleware_disabled_fail_silently(self):
        """
        When the middleware is disabled, an exception is not raised
        if 'fail_silently' is True.
        """
        data = {
            "messages": ["Test message %d" % x for x in range(5)],
            "fail_silently": True,
        }
        show_url = reverse("show_message")
        for level in ("debug", "info", "success", "warning", "error"):
            add_url = reverse("add_message", args=(level,))
            response = self.client.post(add_url, data, follow=True)
            self.assertRedirects(response, show_url)
            self.assertNotIn("messages", response.context)