async def test_follow_double_redirect(self):
        response = await self.async_client.get("/double_redirect_view/", follow=True)
        self.assertRedirects(
            response, "/get_view/", status_code=302, target_status_code=200
        )
        self.assertEqual(len(response.redirect_chain), 2)