async def anum_pages(self):
        """See Paginator.num_pages()."""
        if self._cache_anum_pages is not None:
            return self._cache_anum_pages
        count = await self.acount()
        if count == 0 and not self.allow_empty_first_page:
            self._cache_anum_pages = 0
            return self._cache_anum_pages
        hits = max(1, count - self.orphans)
        num_pages = ceil(hits / self.per_page)

        self._cache_anum_pages = num_pages
        return num_pages