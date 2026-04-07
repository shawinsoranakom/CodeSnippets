async def test_get_data(self):
        response = await self.async_client.get("/get_view/", {"var": "val"})
        self.assertContains(response, "This is a test. val is the value.")