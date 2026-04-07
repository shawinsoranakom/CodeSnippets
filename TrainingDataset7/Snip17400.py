async def test_aiterator_invalid_chunk_size(self):
        msg = "Chunk size must be strictly positive."
        for size in [0, -1]:
            qs = SimpleModel.objects.aiterator(chunk_size=size)
            with self.subTest(size=size), self.assertRaisesMessage(ValueError, msg):
                async for m in qs:
                    pass