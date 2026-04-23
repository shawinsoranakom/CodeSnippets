def test_template_name_suffix(self):
        res = self.client.get("/list/authors/template_name_suffix/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(list(res.context["object_list"]), list(Author.objects.all()))
        self.assertIs(res.context["author_list"], res.context["object_list"])
        self.assertTemplateUsed(res, "generic_views/author_objects.html")