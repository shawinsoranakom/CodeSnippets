def test_m2m_then_reverse_one_to_one_object_ids(self):
        with CaptureQueriesContext(connection) as queries:
            list(Book.objects.prefetch_related("authors__authorwithage"))

        sql = queries[-1]["sql"]
        self.assertWhereContains(sql, self.author1.id)