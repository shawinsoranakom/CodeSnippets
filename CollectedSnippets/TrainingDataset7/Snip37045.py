def test_chunked(self):
        """
        The static view should stream files in chunks to avoid large memory
        usage
        """
        response = self.client.get("/%s/%s" % (self.prefix, "long-line.txt"))
        response_iterator = iter(response)
        first_chunk = next(response_iterator)
        self.assertEqual(len(first_chunk), FileResponse.block_size)
        second_chunk = next(response_iterator)
        response.close()
        # strip() to prevent OS line endings from causing differences
        self.assertEqual(len(second_chunk.strip()), 1449)