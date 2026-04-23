def test_async_streaming(self):
        response = self.client.get("/async_streaming/")
        self.assertEqual(response.status_code, 200)
        msg = (
            "StreamingHttpResponse must consume asynchronous iterators in order to "
            "serve them synchronously. Use a synchronous iterator instead."
        )
        with self.assertWarnsMessage(Warning, msg) as ctx:
            self.assertEqual(b"".join(list(response)), b"streaming content")
        self.assertEqual(ctx.filename, __file__)