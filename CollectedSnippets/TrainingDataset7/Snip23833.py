def test_paginated_invalid_page(self):
        self._make_authors(100)
        res = self.client.get("/list/authors/paginated/?page=frog")
        self.assertEqual(res.status_code, 404)