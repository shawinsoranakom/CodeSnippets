def test_compress_sequence(self):
        data = [{"key": i} for i in range(100)]
        seq = [s.encode() for s in json.JSONEncoder().iterencode(data)]
        original = b"".join(seq)
        batch_size = 256
        batched_seq = (
            original[i : i + batch_size] for i in range(0, len(original), batch_size)
        )
        compressed_chunks = list(text.compress_sequence(batched_seq))
        out = b"".join(compressed_chunks)
        self.assertEqual(gzip.decompress(out), original)
        self.assertLess(len(out), len(original))
        self.assertGreater(len(compressed_chunks), 2)