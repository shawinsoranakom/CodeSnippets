def send_message(self, level):
        """
        Helper that sends a post to the dummy test methods and asserts that a
        message with the level has appeared in the response.
        """
        action_data = {
            ACTION_CHECKBOX_NAME: [1],
            "action": "message_%s" % level,
            "index": 0,
        }

        response = self.client.post(
            reverse("admin:admin_views_usermessenger_changelist"),
            action_data,
            follow=True,
        )
        self.assertContains(
            response, '<li class="%s">Test %s</li>' % (level, level), html=True
        )