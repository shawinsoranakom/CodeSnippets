def test_post_delete_restricted(self):
        album = Album.objects.create(title="Amaryllis")
        Song.objects.create(album=album, name="Unity")
        response = self.client.post(
            reverse("admin:admin_views_album_delete", args=(album.pk,)),
            {"post": "yes"},
        )
        self.assertEqual(Album.objects.count(), 1)
        self.assertContains(
            response,
            "would require deleting the following protected related objects",
        )