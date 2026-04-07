def test_app_model_in_delete_selected_confirmation_body_class(self):
        """
        Ensure app and model tag are correctly read by
        delete_selected_confirmation template
        """
        action_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk],
            "action": "delete_selected",
            "index": 0,
        }
        response = self.client.post(
            reverse("admin:admin_views_section_changelist"), action_data
        )
        self.assertContains(response, '<body class=" app-admin_views model-section ')