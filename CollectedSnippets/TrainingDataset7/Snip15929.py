def test_logentry_get_admin_url(self):
        """
        LogEntry.get_admin_url returns a URL to edit the entry's object or
        None for nonexistent (possibly deleted) models.
        """
        logentry = LogEntry.objects.get(content_type__model__iexact="article")
        expected_url = reverse(
            "admin:admin_utils_article_change", args=(quote(self.a1.pk),)
        )
        self.assertEqual(logentry.get_admin_url(), expected_url)
        self.assertIn("article/%s/change/" % self.a1.pk, logentry.get_admin_url())

        logentry.content_type.model = "nonexistent"
        self.assertIsNone(logentry.get_admin_url())