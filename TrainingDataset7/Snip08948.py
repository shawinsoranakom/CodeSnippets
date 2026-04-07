async def aend_index(self):
        """See Page.end_index()."""
        num_pages = await self.paginator.anum_pages()
        if self.number == num_pages:
            return await self.paginator.acount()
        return self.number * self.paginator.per_page