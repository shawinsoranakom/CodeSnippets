def test_full_request_response_cycle(self):
        """
        With the message middleware enabled, messages are properly stored and
        retrieved across the full request/redirect/response cycle.
        """
        data = {
            "messages": ["Test message %d" % x for x in range(5)],
        }
        show_url = reverse("show_message")
        for level in ("debug", "info", "success", "warning", "error"):
            add_url = reverse("add_message", args=(level,))
            response = self.client.post(add_url, data, follow=True)
            self.assertRedirects(response, show_url)
            self.assertIn("messages", response.context)
            messages = [Message(self.levels[level], msg) for msg in data["messages"]]
            self.assertEqual(list(response.context["messages"]), messages)
            for msg in data["messages"]:
                self.assertContains(response, msg)