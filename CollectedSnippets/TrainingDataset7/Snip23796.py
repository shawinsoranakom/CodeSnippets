def test_create_with_object_url(self):
        res = self.client.post("/edit/artists/create/", {"name": "Rene Magritte"})
        self.assertEqual(res.status_code, 302)
        artist = Artist.objects.get(name="Rene Magritte")
        self.assertRedirects(res, "/detail/artist/%s/" % artist.pk)
        self.assertQuerySetEqual(Artist.objects.all(), [artist])