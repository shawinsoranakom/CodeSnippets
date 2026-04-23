def test_logentry_change_message_localized_datetime_input(self):
        """
        Localized date/time inputs shouldn't affect changed form data
        detection.
        """
        post_data = {
            "site": self.site.pk,
            "title": "Changed",
            "hist": "Some content",
            "created_0": "12/03/2008",
            "created_1": "11:54",
        }
        with translation.override("fr"):
            change_url = reverse(
                "admin:admin_utils_article_change", args=[quote(self.a1.pk)]
            )
            response = self.client.post(change_url, post_data)
            self.assertRedirects(
                response, reverse("admin:admin_utils_article_changelist")
            )
        logentry = LogEntry.objects.filter(
            content_type__model__iexact="article"
        ).latest("id")
        self.assertEqual(logentry.get_change_message(), "Changed Title and History.")