def test_paginated_get_last_page_by_query_string(self):
        self._make_authors(100)
        res = self.client.get("/list/authors/paginated/", {"page": "last"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context["object_list"]), 10)
        self.assertIs(res.context["author_list"], res.context["object_list"])
        self.assertEqual(res.context["author_list"][0].name, "Author 90")
        self.assertEqual(res.context["page_obj"].number, 4)