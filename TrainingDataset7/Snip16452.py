def test_restricted(self):
        album = Album.objects.create(title="Amaryllis")
        song = Song.objects.create(album=album, name="Unity")
        response = self.client.get(
            reverse("admin:admin_views_album_delete", args=(album.pk,))
        )
        self.assertContains(
            response,
            "would require deleting the following protected related objects",
        )
        self.assertContains(
            response,
            '<li>Song: <a href="%s">Unity</a></li>'
            % reverse("admin:admin_views_song_change", args=(song.pk,)),
        )