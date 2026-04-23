def test_update_post(self):
        res = self.client.get("/edit/author/%s/update/" % self.author.pk)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.context["form"], forms.ModelForm)
        self.assertEqual(res.context["object"], self.author)
        self.assertEqual(res.context["author"], self.author)
        self.assertTemplateUsed(res, "generic_views/author_form.html")
        self.assertEqual(res.context["view"].get_form_called_count, 1)

        # Modification with both POST and PUT (browser compatible)
        res = self.client.post(
            "/edit/author/%s/update/" % self.author.pk,
            {"name": "Randall Munroe (xkcd)", "slug": "randall-munroe"},
        )
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, "/list/authors/")
        self.assertQuerySetEqual(
            Author.objects.values_list("name", flat=True), ["Randall Munroe (xkcd)"]
        )