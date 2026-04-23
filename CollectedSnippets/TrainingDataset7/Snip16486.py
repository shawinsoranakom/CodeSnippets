def test_inheritance(self):
        Podcast.objects.create(
            name="This Week in Django", release_date=datetime.date.today()
        )
        response = self.client.get(reverse("admin:admin_views_podcast_changelist"))
        self.assertEqual(response.status_code, 200)