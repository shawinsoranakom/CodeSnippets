def test_duplicate_context_object_name(self):
        res = self.client.get("/list/authors/dupe_context_object_name/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(res.context["object_list"]), list(Author.objects.all()))
        self.assertNotIn("authors", res.context)
        self.assertNotIn("author_list", res.context)
        self.assertTemplateUsed(res, "generic_views/author_list.html")