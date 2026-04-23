async def __aiter__(self):
        page_range = await self.apage_range()
        for page_number in page_range:
            yield await self.apage(page_number)