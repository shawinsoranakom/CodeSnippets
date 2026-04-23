def test_delete_by_post(self):
        res = self.client.get("/edit/author/%s/delete/" % self.author.pk)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["object"], self.author)
        self.assertEqual(res.context["author"], self.author)
        self.assertTemplateUsed(res, "generic_views/author_confirm_delete.html")

        # Deletion with POST
        res = self.client.post("/edit/author/%s/delete/" % self.author.pk)
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, "/list/authors/")
        self.assertQuerySetEqual(Author.objects.all(), [])