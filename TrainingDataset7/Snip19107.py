def test_binary_string(self):
        # Binary strings should be cacheable
        from zlib import compress, decompress

        value = "value_to_be_compressed"
        compressed_value = compress(value.encode())

        # Test set
        cache.set("binary1", compressed_value)
        compressed_result = cache.get("binary1")
        self.assertEqual(compressed_value, compressed_result)
        self.assertEqual(value, decompress(compressed_result).decode())

        # Test add
        self.assertIs(cache.add("binary1-add", compressed_value), True)
        compressed_result = cache.get("binary1-add")
        self.assertEqual(compressed_value, compressed_result)
        self.assertEqual(value, decompress(compressed_result).decode())

        # Test set_many
        cache.set_many({"binary1-set_many": compressed_value})
        compressed_result = cache.get("binary1-set_many")
        self.assertEqual(compressed_value, compressed_result)
        self.assertEqual(value, decompress(compressed_result).decode())