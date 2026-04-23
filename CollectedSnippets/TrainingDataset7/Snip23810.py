def test_update_with_redirect(self):
        res = self.client.post(
            "/edit/author/%s/update/redirect/" % self.author.pk,
            {"name": "Randall Munroe (author of xkcd)", "slug": "randall-munroe"},
        )
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, "/edit/authors/create/")
        self.assertQuerySetEqual(
            Author.objects.values_list("name", flat=True),
            ["Randall Munroe (author of xkcd)"],
        )