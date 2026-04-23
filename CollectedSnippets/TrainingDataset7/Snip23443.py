def setUp(self):
        self.client.force_login(self.superuser)

        e = Episode.objects.create(name="This Week in Django")
        self.episode_pk = e.pk
        m = Media(content_object=e, url="http://example.com/podcast.mp3")
        m.save()
        self.mp3_media_pk = m.pk

        m = Media(content_object=e, url="http://example.com/logo.png")
        m.save()
        self.png_media_pk = m.pk