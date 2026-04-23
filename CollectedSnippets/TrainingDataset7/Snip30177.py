def test_m2m_prefetching_iterator_with_chunks(self):
        with self.assertNumQueries(3):
            authors = [
                b.authors.first()
                for b in Book.objects.prefetch_related("authors").iterator(chunk_size=2)
            ]
        self.assertEqual(
            authors,
            [self.author1, self.author1, self.author3, self.author4],
        )