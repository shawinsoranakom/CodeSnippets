def test_create_with_special_properties(self):
        res = self.client.get("/edit/authors/create/special/")
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.context["form"], views.AuthorForm)
        self.assertNotIn("object", res.context)
        self.assertNotIn("author", res.context)
        self.assertTemplateUsed(res, "generic_views/form.html")

        res = self.client.post(
            "/edit/authors/create/special/",
            {"name": "Randall Munroe", "slug": "randall-munroe"},
        )
        self.assertEqual(res.status_code, 302)
        obj = Author.objects.get(slug="randall-munroe")
        self.assertRedirects(res, reverse("author_detail", kwargs={"pk": obj.pk}))
        self.assertQuerySetEqual(Author.objects.all(), [obj])