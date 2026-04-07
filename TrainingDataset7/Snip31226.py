def test_generator_cache(self):
        generator = (str(i) for i in range(10))
        response = HttpResponse(content=generator)
        self.assertEqual(response.content, b"0123456789")
        with self.assertRaises(StopIteration):
            next(generator)

        cache.set("my-response-key", response)
        response = cache.get("my-response-key")
        self.assertEqual(response.content, b"0123456789")