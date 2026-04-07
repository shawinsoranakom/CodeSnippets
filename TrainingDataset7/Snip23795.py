def test_create_invalid(self):
        res = self.client.post(
            "/edit/authors/create/", {"name": "A" * 101, "slug": "randall-munroe"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "generic_views/author_form.html")
        self.assertEqual(len(res.context["form"].errors), 1)
        self.assertEqual(Author.objects.count(), 0)