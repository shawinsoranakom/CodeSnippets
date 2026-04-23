def test_iterator_invalid_chunk_size(self):
        for size in (0, -1):
            with self.subTest(size=size):
                with self.assertRaisesMessage(
                    ValueError, "Chunk size must be strictly positive."
                ):
                    Article.objects.iterator(chunk_size=size)