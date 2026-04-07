def test_update_with_interpolated_redirect(self):
        res = self.client.post(
            "/edit/author/%s/update/interpolate_redirect/" % self.author.pk,
            {"name": "Randall Munroe (author of xkcd)", "slug": "randall-munroe"},
        )
        self.assertQuerySetEqual(
            Author.objects.values_list("name", flat=True),
            ["Randall Munroe (author of xkcd)"],
        )
        self.assertEqual(res.status_code, 302)
        pk = Author.objects.first().pk
        self.assertRedirects(res, "/edit/author/%s/update/" % pk)
        # Also test with escaped chars in URL
        res = self.client.post(
            "/edit/author/%s/update/interpolate_redirect_nonascii/" % self.author.pk,
            {"name": "John Doe", "slug": "john-doe"},
        )
        self.assertEqual(res.status_code, 302)
        pk = Author.objects.get(name="John Doe").pk
        self.assertRedirects(res, "/%C3%A9dit/author/{}/update/".format(pk))