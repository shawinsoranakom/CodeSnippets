async def test_post_data(self):
        response = await self.async_client.post("/post_view/", {"value": 37})
        self.assertContains(response, "Data received: 37 is the value.")