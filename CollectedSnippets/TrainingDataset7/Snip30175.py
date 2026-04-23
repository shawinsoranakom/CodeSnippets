def test_filter_deferred(self):
        """
        Related filtering of prefetched querysets is deferred on m2m and
        reverse m2o relations until necessary.
        """
        add_q = Query.add_q
        for relation in ["authors", "first_time_authors"]:
            with self.subTest(relation=relation):
                with mock.patch.object(
                    Query,
                    "add_q",
                    autospec=True,
                    side_effect=lambda self, q, reuse_all: add_q(self, q),
                ) as add_q_mock:
                    list(Book.objects.prefetch_related(relation))
                    self.assertEqual(add_q_mock.call_count, 1)