def test_media_from_actions_form(self):
        """
        The action form's media is included in the changelist view's media.
        """
        response = self.client.get(reverse("admin:admin_views_subscriber_changelist"))
        media_path = MediaActionForm.Media.js[0]
        self.assertIsInstance(response.context["action_form"], MediaActionForm)
        self.assertIn("media", response.context)
        self.assertIn(media_path, response.context["media"]._js)
        self.assertContains(response, media_path)