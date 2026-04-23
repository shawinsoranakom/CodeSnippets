def test_paginated_page_out_of_range(self):
        self._make_authors(100)
        res = self.client.get("/list/authors/paginated/42/")
        self.assertEqual(res.status_code, 404)