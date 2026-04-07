async def avalidate_number(self, number):
        num_pages = await self.anum_pages()
        return self._validate_number(number, num_pages)