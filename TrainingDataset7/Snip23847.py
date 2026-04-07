def test_paginated_list_view_does_not_load_entire_table(self):
        # Regression test for #17535
        self._make_authors(3)
        # 1 query for authors
        with self.assertNumQueries(1):
            self.client.get("/list/authors/notempty/")
        # same as above + 1 query to test if authors exist + 1 query for
        # pagination
        with self.assertNumQueries(3):
            self.client.get("/list/authors/notempty/paginated/")