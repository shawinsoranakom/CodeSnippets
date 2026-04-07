async def aget_elided_page_range(self, number=1, *, on_each_side=3, on_ends=2):
        number = await self.avalidate_number(number)
        num_pages = await self.anum_pages()
        page_range = await self.apage_range()
        for page in self._get_elided_page_range(
            number, num_pages, page_range, on_each_side, on_ends
        ):
            yield page