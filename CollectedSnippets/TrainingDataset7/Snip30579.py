def test_get_clears_ordering(self):
        """
        get() should clear ordering for optimization purposes.
        """
        with CaptureQueriesContext(connection) as captured_queries:
            Author.objects.order_by("name").get(pk=self.a1.pk)
        self.assertNotIn("order by", captured_queries[0]["sql"].lower())