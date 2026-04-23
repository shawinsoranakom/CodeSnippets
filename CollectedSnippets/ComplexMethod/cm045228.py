async def fill_id(self, page: Page, identifier: str, value: str, press_enter: bool = True) -> None:
        """
        Fill the element with the given identifier with the specified value.

        Args:
            page (Page): The Playwright page object.
            identifier (str): The element identifier.
            value (str): The value to fill.
        """
        assert page is not None
        target = page.locator(f"[__elementId='{identifier}']")

        # See if it exists
        try:
            await target.wait_for(timeout=5000)
        except TimeoutError:
            raise ValueError("No such element.") from None

        # Fill it
        await target.scroll_into_view_if_needed()
        box = cast(Dict[str, Union[int, float]], await target.bounding_box())

        if self.animate_actions:
            await self.add_cursor_box(page, identifier)
            # Move cursor to the box slowly
            start_x, start_y = self.last_cursor_position
            end_x, end_y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            await self.gradual_cursor_animation(page, start_x, start_y, end_x, end_y)
            await asyncio.sleep(0.1)

        # Focus on the element
        await target.focus()
        if self.animate_actions:
            # fill char by char to mimic human speed for short text and type fast for long text
            if len(value) < 100:
                delay_typing_speed = 50 + 100 * random.random()
            else:
                delay_typing_speed = 10
            await target.press_sequentially(value, delay=delay_typing_speed)
        else:
            try:
                await target.fill(value)
            except PlaywrightError:
                await target.press_sequentially(value)
        if press_enter:
            await target.press("Enter")

        if self.animate_actions:
            await self.remove_cursor_box(page, identifier)