def test_default_redirect(self):
        """
        Actions which don't return an HttpResponse are redirected to the same
        page, retaining the querystring (which may contain changelist info).
        """
        action_data = {
            ACTION_CHECKBOX_NAME: [self.s1.pk],
            "action": "external_mail",
            "index": 0,
        }
        url = reverse("admin:admin_views_externalsubscriber_changelist") + "?o=1"
        response = self.client.post(url, action_data)
        self.assertRedirects(response, url)