async def test_async_view(self):
        """Calling an async view down the asynchronous path."""
        response = await self.async_client.get("/async_regular/")
        self.assertEqual(response.status_code, 200)