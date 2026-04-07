def test_paginated_non_queryset(self):
        res = self.client.get("/list/dict/paginated/")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context["object_list"]), 1)