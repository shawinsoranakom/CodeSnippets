def test_force_bytes_memory_view(self):
        data = b"abc"
        result = force_bytes(memoryview(data))
        # Type check is needed because memoryview(bytes) == bytes.
        self.assertIs(type(result), bytes)
        self.assertEqual(result, data)