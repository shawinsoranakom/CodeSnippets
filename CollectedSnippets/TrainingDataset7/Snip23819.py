def test_delete_with_interpolated_redirect(self):
        res = self.client.post(
            "/edit/author/%s/delete/interpolate_redirect/" % self.author.pk
        )
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, "/edit/authors/create/?deleted=%s" % self.author.pk)
        self.assertQuerySetEqual(Author.objects.all(), [])
        # Also test with escaped chars in URL
        a = Author.objects.create(
            **{"name": "Randall Munroe", "slug": "randall-munroe"}
        )
        res = self.client.post(
            "/edit/author/{}/delete/interpolate_redirect_nonascii/".format(a.pk)
        )
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, "/%C3%A9dit/authors/create/?deleted={}".format(a.pk))