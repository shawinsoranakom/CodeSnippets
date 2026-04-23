def test_context_object_name(self):
        res = self.client.get("/list/authors/context_object_name/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(res.context["object_list"]), list(Author.objects.all()))
        self.assertNotIn("authors", res.context)
        self.assertIs(res.context["author_list"], res.context["object_list"])
        self.assertTemplateUsed(res, "generic_views/author_list.html")