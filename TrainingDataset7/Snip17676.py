async def test_login_required_next_url_async_view(self):
        await self.test_login_required_async_view(login_url="/somewhere/")