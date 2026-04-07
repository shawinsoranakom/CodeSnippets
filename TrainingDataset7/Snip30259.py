def test_window_not_supported(self):
        authors = Author.objects.all()
        msg = (
            "Prefetching from a limited queryset is only supported on backends that "
            "support window functions."
        )
        with self.assertRaisesMessage(NotSupportedError, msg):
            list(Book.objects.prefetch_related(Prefetch("authors", authors[1:])))