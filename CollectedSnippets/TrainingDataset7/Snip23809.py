def test_update_with_object_url(self):
        a = Artist.objects.create(name="Rene Magritte")
        res = self.client.post(
            "/edit/artists/%s/update/" % a.pk, {"name": "Rene Magritte"}
        )
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, "/detail/artist/%s/" % a.pk)
        self.assertQuerySetEqual(Artist.objects.all(), [a])