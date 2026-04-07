def test_custom_function_action_streaming_response(self):
        """A custom action may return a StreamingHttpResponse."""
        action_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk],
            "action": "download",
            "index": 0,
        }
        response = self.client.post(
            reverse("admin:admin_views_externalsubscriber_changelist"), action_data
        )
        content = b"".join(list(response))
        self.assertEqual(content, b"This is the content of the file")
        self.assertEqual(response.status_code, 200)