def test_create_restricted(self):
        res = self.client.post(
            "/edit/authors/create/restricted/",
            {"name": "Randall Munroe", "slug": "randall-munroe"},
        )
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(
            res, "/accounts/login/?next=/edit/authors/create/restricted/"
        )