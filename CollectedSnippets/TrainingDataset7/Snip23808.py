def test_update_invalid(self):
        res = self.client.post(
            "/edit/author/%s/update/" % self.author.pk,
            {"name": "A" * 101, "slug": "randall-munroe"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "generic_views/author_form.html")
        self.assertEqual(len(res.context["form"].errors), 1)
        self.assertQuerySetEqual(Author.objects.all(), [self.author])
        self.assertEqual(res.context["view"].get_form_called_count, 1)