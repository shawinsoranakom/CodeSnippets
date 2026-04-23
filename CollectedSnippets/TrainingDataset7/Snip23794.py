def test_create(self):
        res = self.client.get("/edit/authors/create/")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.context["form"], forms.ModelForm)
        self.assertIsInstance(res.context["view"], View)
        self.assertNotIn("object", res.context)
        self.assertNotIn("author", res.context)
        self.assertTemplateUsed(res, "generic_views/author_form.html")

        res = self.client.post(
            "/edit/authors/create/",
            {"name": "Randall Munroe", "slug": "randall-munroe"},
        )
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, "/list/authors/")
        self.assertQuerySetEqual(
            Author.objects.values_list("name", flat=True), ["Randall Munroe"]
        )