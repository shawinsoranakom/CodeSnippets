def test_m2m_then_m2m_object_ids(self):
        with CaptureQueriesContext(connection) as queries:
            list(Book.objects.prefetch_related("authors__favorite_authors"))

        sql = queries[-1]["sql"]
        self.assertWhereContains(sql, self.author1.name)