def test_streaming_response(self):
        r = StreamingHttpResponse(iter(["hello", "world"]))

        # iterating over the response itself yields bytestring chunks.
        chunks = list(r)
        self.assertEqual(chunks, [b"hello", b"world"])
        for chunk in chunks:
            self.assertIsInstance(chunk, bytes)

        # and the response can only be iterated once.
        self.assertEqual(list(r), [])

        # even when a sequence that can be iterated many times, like a list,
        # is given as content.
        r = StreamingHttpResponse(["abc", "def"])
        self.assertEqual(list(r), [b"abc", b"def"])
        self.assertEqual(list(r), [])

        # iterating over strings still yields bytestring chunks.
        r.streaming_content = iter(["hello", "café"])
        chunks = list(r)
        # '\xc3\xa9' == unichr(233).encode()
        self.assertEqual(chunks, [b"hello", b"caf\xc3\xa9"])
        for chunk in chunks:
            self.assertIsInstance(chunk, bytes)

        # streaming responses don't have a `content` attribute.
        self.assertFalse(hasattr(r, "content"))

        # and you can't accidentally assign to a `content` attribute.
        with self.assertRaises(AttributeError):
            r.content = "xyz"

        # but they do have a `streaming_content` attribute.
        self.assertTrue(hasattr(r, "streaming_content"))

        # that exists so we can check if a response is streaming, and wrap or
        # replace the content iterator.
        r.streaming_content = iter(["abc", "def"])
        r.streaming_content = (chunk.upper() for chunk in r.streaming_content)
        self.assertEqual(list(r), [b"ABC", b"DEF"])

        # coercing a streaming response to bytes doesn't return a complete HTTP
        # message like a regular response does. it only gives us the headers.
        r = StreamingHttpResponse(iter(["hello", "world"]))
        self.assertEqual(bytes(r), b"Content-Type: text/html; charset=utf-8")

        # and this won't consume its content.
        self.assertEqual(list(r), [b"hello", b"world"])

        # additional content cannot be written to the response.
        r = StreamingHttpResponse(iter(["hello", "world"]))
        with self.assertRaises(Exception):
            r.write("!")

        # and we can't tell the current position.
        with self.assertRaises(Exception):
            r.tell()

        r = StreamingHttpResponse(iter(["hello", "world"]))
        self.assertEqual(r.getvalue(), b"helloworld")