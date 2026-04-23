def test_update_with_special_properties(self):
        res = self.client.get("/edit/author/%s/update/special/" % self.author.pk)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.context["form"], views.AuthorForm)
        self.assertEqual(res.context["object"], self.author)
        self.assertEqual(res.context["thingy"], self.author)
        self.assertNotIn("author", res.context)
        self.assertTemplateUsed(res, "generic_views/form.html")

        res = self.client.post(
            "/edit/author/%s/update/special/" % self.author.pk,
            {"name": "Randall Munroe (author of xkcd)", "slug": "randall-munroe"},
        )
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, "/detail/author/%s/" % self.author.pk)
        self.assertQuerySetEqual(
            Author.objects.values_list("name", flat=True),
            ["Randall Munroe (author of xkcd)"],
        )