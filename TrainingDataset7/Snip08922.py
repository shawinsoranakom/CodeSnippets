async def apage_range(self):
        """See Paginator.page_range()"""
        num_pages = await self.anum_pages()
        return range(1, num_pages + 1)