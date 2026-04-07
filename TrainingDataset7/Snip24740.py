async def test_sync_view(self):
        """Calling a sync view down the asynchronous path."""
        response = await self.async_client.get("/regular/")
        self.assertEqual(response.status_code, 200)