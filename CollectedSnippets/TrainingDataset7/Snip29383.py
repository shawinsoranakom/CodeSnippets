async def aprevious_page_number(self):
        if not await self.ahas_previous():
            return None
        return await super().aprevious_page_number()