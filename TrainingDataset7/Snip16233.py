def test_included_app_list_template_context_fully_set(self):
        # All context variables should be set when rendering the sidebar.
        url = reverse("test_with_sidebar:auth_user_changelist")
        with self.assertNoLogs("django.template", "DEBUG"):
            self.client.get(url)