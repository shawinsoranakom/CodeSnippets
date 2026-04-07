def test_create_with_redirect(self):
        res = self.client.post(
            "/edit/authors/create/redirect/",
            {"name": "Randall Munroe", "slug": "randall-munroe"},
        )
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, "/edit/authors/create/")
        self.assertQuerySetEqual(
            Author.objects.values_list("name", flat=True), ["Randall Munroe"]
        )