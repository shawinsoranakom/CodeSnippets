def test_filter_deferred(self):
        """
        Related filtering of prefetched querysets is deferred until necessary.
        """
        add_q = Query.add_q
        with mock.patch.object(
            Query,
            "add_q",
            autospec=True,
            side_effect=lambda self, q, reuse_all: add_q(self, q),
        ) as add_q_mock:
            list(
                House.objects.prefetch_related(
                    Prefetch("occupants", queryset=Person.objects.all())
                )
            )
            self.assertEqual(add_q_mock.call_count, 1)