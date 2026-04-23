def test_multiple_posts(self):
        """
        Messages persist properly when multiple POSTs are made before a GET.
        """
        data = {
            "messages": ["Test message %d" % x for x in range(5)],
        }
        show_url = reverse("show_message")
        messages = []
        for level in ("debug", "info", "success", "warning", "error"):
            messages.extend(
                Message(self.levels[level], msg) for msg in data["messages"]
            )
            add_url = reverse("add_message", args=(level,))
            self.client.post(add_url, data)
        response = self.client.get(show_url)
        self.assertIn("messages", response.context)
        self.assertEqual(list(response.context["messages"]), messages)
        for msg in data["messages"]:
            self.assertContains(response, msg)