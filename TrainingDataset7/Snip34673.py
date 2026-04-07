async def test_body_read_on_get_data(self):
        response = await self.async_client.get("/post_view/")
        self.assertContains(response, "Viewing GET page.")