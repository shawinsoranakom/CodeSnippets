def test_m2m_prefetching_iterator_without_chunks_error(self):
        msg = (
            "chunk_size must be provided when using QuerySet.iterator() after "
            "prefetch_related()."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Book.objects.prefetch_related("authors").iterator()