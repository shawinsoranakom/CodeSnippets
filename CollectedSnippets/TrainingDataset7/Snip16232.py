def test_sidebar_aria_current_page_missing_without_request_context_processor(self):
        url = reverse("test_with_sidebar:auth_user_changelist")
        response = self.client.get(url)
        self.assertContains(
            response, '<nav class="sticky" id="nav-sidebar" aria-label="Sidebar">'
        )
        # Does not include aria-current attribute.
        self.assertContains(response, '<a href="%s">Users</a>' % url)