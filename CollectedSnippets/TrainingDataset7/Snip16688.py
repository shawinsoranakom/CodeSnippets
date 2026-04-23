def test_message_extra_tags(self):
        action_data = {
            ACTION_CHECKBOX_NAME: [1],
            "action": "message_extra_tags",
            "index": 0,
        }

        response = self.client.post(
            reverse("admin:admin_views_usermessenger_changelist"),
            action_data,
            follow=True,
        )
        self.assertContains(
            response, '<li class="extra_tag info">Test tags</li>', html=True
        )