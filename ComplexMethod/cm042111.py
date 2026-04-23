async def test_start_and_stop(self):
        """Test browser start and stop functionality."""
        assert self.browser.playwright is not None
        assert self.browser.browser_instance is not None
        assert self.browser.browser_ctx is not None
        assert self.browser.page is not None

        await self.async_teardown()

        assert self.browser.playwright is None
        assert self.browser.browser_instance is None
        assert self.browser.browser_ctx is None