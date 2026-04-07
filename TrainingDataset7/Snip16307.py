def test_change_list_sorting_override_model_admin(self):
        # Test ordering on Model Admin is respected, and overrides Model Meta
        dt = datetime.datetime.now()
        p1 = Podcast.objects.create(name="A", release_date=dt)
        p2 = Podcast.objects.create(name="B", release_date=dt - datetime.timedelta(10))
        link1 = reverse("admin:admin_views_podcast_change", args=(p1.pk,))
        link2 = reverse("admin:admin_views_podcast_change", args=(p2.pk,))

        response = self.client.get(reverse("admin:admin_views_podcast_changelist"), {})
        self.assertContentBefore(response, link1, link2)