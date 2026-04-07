async def test_sync_streaming(self):
        response = await self.async_client.get("/streaming/")
        self.assertEqual(response.status_code, 200)
        msg = (
            "StreamingHttpResponse must consume synchronous iterators in order to "
            "serve them asynchronously. Use an asynchronous iterator instead."
        )
        with self.assertWarnsMessage(Warning, msg) as ctx:
            self.assertEqual(
                b"".join([chunk async for chunk in response]), b"streaming content"
            )
        self.assertEqual(ctx.filename, __file__)