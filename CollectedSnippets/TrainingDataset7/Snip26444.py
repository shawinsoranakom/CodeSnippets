def test_with_template_response(self):
        data = {
            "messages": ["Test message %d" % x for x in range(5)],
        }
        show_url = reverse("show_template_response")
        for level in self.levels:
            add_url = reverse("add_template_response", args=(level,))
            response = self.client.post(add_url, data, follow=True)
            self.assertRedirects(response, show_url)
            self.assertIn("messages", response.context)
            for msg in data["messages"]:
                self.assertContains(response, msg)

            # there shouldn't be any messages on second GET request
            response = self.client.get(show_url)
            for msg in data["messages"]:
                self.assertNotContains(response, msg)