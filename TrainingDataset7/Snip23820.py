def test_delete_with_special_properties(self):
        res = self.client.get("/edit/author/%s/delete/special/" % self.author.pk)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["object"], self.author)
        self.assertEqual(res.context["thingy"], self.author)
        self.assertNotIn("author", res.context)
        self.assertTemplateUsed(res, "generic_views/confirm_delete.html")

        res = self.client.post("/edit/author/%s/delete/special/" % self.author.pk)
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, "/list/authors/")
        self.assertQuerySetEqual(Author.objects.all(), [])