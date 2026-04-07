def test_recentactions_without_content_type(self):
        """
        If a LogEntry is missing content_type it will not display it in span
        tag under the hyperlink.
        """
        response = self.client.get(reverse("admin:index"))
        link = reverse("admin:admin_utils_article_change", args=(quote(self.a1.pk),))
        should_contain = """<a href="%s">%s</a>""" % (
            escape(link),
            escape(str(self.a1)),
        )
        self.assertContains(response, should_contain)
        should_contain = "Article"
        self.assertContains(response, should_contain)
        logentry = LogEntry.objects.get(content_type__model__iexact="article")
        # If the log entry doesn't have a content type it should still be
        # possible to view the Recent Actions part (#10275).
        logentry.content_type = None
        logentry.save()

        should_contain = should_contain.encode()
        counted_presence_before = response.content.count(should_contain)
        response = self.client.get(reverse("admin:index"))
        counted_presence_after = response.content.count(should_contain)
        self.assertEqual(counted_presence_before - 1, counted_presence_after)