def test_paginated_queryset_shortdata(self):
        # Short datasets also result in a paginated view.
        res = self.client.get("/list/authors/paginated/")
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, "generic_views/author_list.html")
        self.assertEqual(list(res.context["object_list"]), list(Author.objects.all()))
        self.assertIs(res.context["author_list"], res.context["object_list"])
        self.assertEqual(res.context["page_obj"].number, 1)
        self.assertEqual(res.context["paginator"].num_pages, 1)
        self.assertFalse(res.context["is_paginated"])