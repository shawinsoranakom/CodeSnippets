async def test_redirect(self):
        response = await self.async_client.get("/redirect_view/")
        self.assertEqual(response.status_code, 302)