def test_delete_with_form_as_post(self):
        res = self.client.get("/edit/author/%s/delete/form/" % self.author.pk)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["object"], self.author)
        self.assertEqual(res.context["author"], self.author)
        self.assertTemplateUsed(res, "generic_views/author_confirm_delete.html")
        res = self.client.post(
            "/edit/author/%s/delete/form/" % self.author.pk, data={"confirm": True}
        )
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, "/list/authors/")
        self.assertSequenceEqual(Author.objects.all(), [])