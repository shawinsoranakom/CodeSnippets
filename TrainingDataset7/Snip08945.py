async def anext_page_number(self):
        return await self.paginator.avalidate_number(self.number + 1)