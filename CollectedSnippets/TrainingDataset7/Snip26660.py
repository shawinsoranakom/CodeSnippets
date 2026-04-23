def test_compress_deterministic(self):
        """
        Compression results are the same for the same content and don't
        include a modification time (since that would make the results
        of compression non-deterministic and prevent
        ConditionalGetMiddleware from recognizing conditional matches
        on gzipped content).
        """

        class DeterministicGZipMiddleware(GZipMiddleware):
            max_random_bytes = 0

        r1 = DeterministicGZipMiddleware(self.get_response)(self.req)
        r2 = DeterministicGZipMiddleware(self.get_response)(self.req)
        self.assertEqual(r1.content, r2.content)
        self.assertEqual(self.get_mtime(r1.content), 0)
        self.assertEqual(self.get_mtime(r2.content), 0)