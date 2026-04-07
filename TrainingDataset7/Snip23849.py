def test_paginated_list_view_returns_useful_message_on_invalid_page(self):
        # test for #19240
        # tests that source exception's message is included in page
        self._make_authors(1)
        res = self.client.get("/list/authors/paginated/2/")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(
            res.context.get("reason"), "Invalid page (2): That page contains no results"
        )