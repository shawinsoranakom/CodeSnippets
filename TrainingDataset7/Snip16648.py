def test_app_model_in_delete_confirmation_body_class(self):
        """
        Ensure app and model tag are correctly read by delete_confirmation
        template
        """
        response = self.client.get(
            reverse("admin:admin_views_section_delete", args=(self.s1.pk,))
        )
        self.assertContains(response, '<body class=" app-admin_views model-section ')