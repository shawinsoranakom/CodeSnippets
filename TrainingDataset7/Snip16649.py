def test_app_model_in_app_index_body_class(self):
        """
        Ensure app and model tag are correctly read by app_index template
        """
        response = self.client.get(reverse("admin:app_list", args=("admin_views",)))
        self.assertContains(response, '<body class=" dashboard app-admin_views')