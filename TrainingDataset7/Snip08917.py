async def aget_page(self, number):
        """See Paginator.get_page()."""
        try:
            number = await self.avalidate_number(number)
        except PageNotAnInteger:
            number = 1
        except EmptyPage:
            number = await self.anum_pages()
        return await self.apage(number)