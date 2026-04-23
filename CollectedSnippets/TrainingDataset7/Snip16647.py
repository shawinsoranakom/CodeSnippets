def test_app_model_in_list_body_class(self):
        """
        Ensure app and model tag are correctly read by change_list template
        """
        response = self.client.get(reverse("admin:admin_views_section_changelist"))
        self.assertContains(response, '<body class=" app-admin_views model-section ')