def test_logentry_change_message(self):
        """
        LogEntry.change_message is stored as a dumped JSON structure to be able
        to get the message dynamically translated at display time.
        """
        post_data = {
            "site": self.site.pk,
            "title": "Changed",
            "hist": "Some content",
            "created_0": "2008-03-12",
            "created_1": "11:54",
        }
        change_url = reverse(
            "admin:admin_utils_article_change", args=[quote(self.a1.pk)]
        )
        response = self.client.post(change_url, post_data)
        self.assertRedirects(response, reverse("admin:admin_utils_article_changelist"))
        logentry = LogEntry.objects.filter(
            content_type__model__iexact="article"
        ).latest("id")
        self.assertEqual(logentry.get_change_message(), "Changed Title and History.")
        with translation.override("fr"):
            self.assertEqual(
                logentry.get_change_message(), "Modification de Title et Historique."
            )

        add_url = reverse("admin:admin_utils_article_add")
        post_data["title"] = "New"
        response = self.client.post(add_url, post_data)
        self.assertRedirects(response, reverse("admin:admin_utils_article_changelist"))
        logentry = LogEntry.objects.filter(
            content_type__model__iexact="article"
        ).latest("id")
        self.assertEqual(logentry.get_change_message(), "Added.")
        with translation.override("fr"):
            self.assertEqual(logentry.get_change_message(), "Ajout.")