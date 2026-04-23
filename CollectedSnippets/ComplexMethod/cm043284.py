async def _handle_full_page_scan(self, page: Page, scroll_delay: float = 0.1, max_scroll_steps: Optional[int] = None):
        """
        Helper method to handle full page scanning.

        How it works:
        1. Get the viewport height.
        2. Scroll to the bottom of the page.
        3. Get the total height of the page.
        4. Scroll back to the top of the page.
        5. Scroll to the bottom of the page again.
        6. Continue scrolling until the bottom of the page is reached.

        Args:
            page (Page): The Playwright page object
            scroll_delay (float): The delay between page scrolls
            max_scroll_steps (Optional[int]): Maximum number of scroll steps to perform. Defaults to 10 to prevent infinite scroll hangs.

        """
        # Default to 10 steps to prevent infinite scroll on dynamic pages
        if max_scroll_steps is None:
            max_scroll_steps = 10

        try:
            viewport_size = page.viewport_size
            if viewport_size is None:
                await page.set_viewport_size(
                    {"width": self.browser_config.viewport_width, "height": self.browser_config.viewport_height}
                )
                viewport_size = page.viewport_size

            viewport_height = viewport_size.get(
                "height", self.browser_config.viewport_height
            )
            current_position = viewport_height

            # await page.evaluate(f"window.scrollTo(0, {current_position})")
            await self.safe_scroll(page, 0, current_position, delay=scroll_delay)
            # await self.csp_scroll_to(page, 0, current_position)
            # await asyncio.sleep(scroll_delay)

            # total_height = await page.evaluate("document.documentElement.scrollHeight")
            dimensions = await self.get_page_dimensions(page)
            total_height = dimensions["height"]

            scroll_step_count = 0
            while current_position < total_height:
                #### 
                # NEW FEATURE: Check if we've reached the maximum allowed scroll steps
                # This prevents infinite scrolling on very long pages or infinite scroll scenarios
                # If max_scroll_steps is None, this check is skipped (unlimited scrolling - original behavior)
                ####
                if max_scroll_steps is not None and scroll_step_count >= max_scroll_steps:
                    break
                current_position = min(current_position + viewport_height, total_height)
                await self.safe_scroll(page, 0, current_position, delay=scroll_delay)

                # Increment the step counter for max_scroll_steps tracking
                scroll_step_count += 1

                # await page.evaluate(f"window.scrollTo(0, {current_position})")
                # await asyncio.sleep(scroll_delay)

                # new_height = await page.evaluate("document.documentElement.scrollHeight")
                dimensions = await self.get_page_dimensions(page)
                new_height = dimensions["height"]

                if new_height > total_height:
                    total_height = new_height

            # await page.evaluate("window.scrollTo(0, 0)")
            await self.safe_scroll(page, 0, 0)

        except Exception as e:
            self.logger.warning(
                message="Failed to perform full page scan: {error}",
                tag="PAGE_SCAN",
                params={"error": str(e)},
            )
        else:
            # await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self.safe_scroll(page, 0, total_height)