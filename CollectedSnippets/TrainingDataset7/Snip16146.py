def test_model_without_action_still_has_jquery(self):
        """
        A ModelAdmin without any actions still has jQuery included on the page.
        """
        response = self.client.get(
            reverse("admin:admin_views_oldsubscriber_changelist")
        )
        self.assertIsNone(response.context["action_form"])
        self.assertContains(
            response,
            "jquery.min.js",
            msg_prefix=(
                "jQuery missing from admin pages for model with no admin actions"
            ),
        )