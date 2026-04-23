async def anext_page_number(self):
        if not await self.ahas_next():
            return None
        return await super().anext_page_number()