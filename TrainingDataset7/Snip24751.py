async def test_async_streaming(self):
        response = await self.async_client.get("/async_streaming/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            b"".join([chunk async for chunk in response]), b"streaming content"
        )