async def ahas_next(self):
        num_pages = await self.paginator.anum_pages()
        return self.number < num_pages