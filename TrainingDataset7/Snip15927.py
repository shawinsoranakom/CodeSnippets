def test_logentry_change_message_formsets(self):
        """
        All messages for changed formsets are logged in a change message.
        """
        a2 = Article.objects.create(
            site=self.site,
            title="Title second article",
            created=datetime(2012, 3, 18, 11, 54),
        )
        post_data = {
            "domain": "example.com",  # domain changed
            "admin_articles-TOTAL_FORMS": "5",
            "admin_articles-INITIAL_FORMS": "2",
            "admin_articles-MIN_NUM_FORMS": "0",
            "admin_articles-MAX_NUM_FORMS": "1000",
            # Changed title for 1st article
            "admin_articles-0-id": str(self.a1.pk),
            "admin_articles-0-site": str(self.site.pk),
            "admin_articles-0-title": "Changed Title",
            # Second article is deleted
            "admin_articles-1-id": str(a2.pk),
            "admin_articles-1-site": str(self.site.pk),
            "admin_articles-1-title": "Title second article",
            "admin_articles-1-DELETE": "on",
            # A new article is added
            "admin_articles-2-site": str(self.site.pk),
            "admin_articles-2-title": "Added article",
        }
        change_url = reverse(
            "admin:admin_utils_site_change", args=[quote(self.site.pk)]
        )
        response = self.client.post(change_url, post_data)
        self.assertRedirects(response, reverse("admin:admin_utils_site_changelist"))
        self.assertSequenceEqual(Article.objects.filter(pk=a2.pk), [])
        logentry = LogEntry.objects.filter(content_type__model__iexact="site").latest(
            "action_time"
        )
        self.assertEqual(
            json.loads(logentry.change_message),
            [
                {"changed": {"fields": ["Domain"]}},
                {"added": {"object": "Added article", "name": "article"}},
                {
                    "changed": {
                        "fields": ["Title", "not_a_form_field"],
                        "object": "Changed Title",
                        "name": "article",
                    }
                },
                {"deleted": {"object": "Title second article", "name": "article"}},
            ],
        )
        self.assertEqual(
            logentry.get_change_message(),
            "Changed Domain. Added article “Added article”. "
            "Changed Title and not_a_form_field for article “Changed Title”. "
            "Deleted article “Title second article”.",
        )

        with translation.override("fr"):
            self.assertEqual(
                logentry.get_change_message(),
                "Modification de Domain. Ajout de article « Added article ». "
                "Modification de Title et not_a_form_field pour l'objet "
                "article « Changed Title ». "
                "Suppression de article « Title second article ».",
            )