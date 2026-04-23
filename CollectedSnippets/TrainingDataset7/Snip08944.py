async def ahas_other_pages(self):
        has_previous = await self.ahas_previous()
        has_next = await self.ahas_next()
        return has_previous or has_next