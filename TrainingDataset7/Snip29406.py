async def check_indexes_async(self, params, page_num, indexes):
        """See check_indexes."""
        paginator = AsyncPaginator(*params)
        if page_num == "first":
            page_num = 1
        elif page_num == "last":
            page_num = await paginator.anum_pages()
        page = await paginator.apage(page_num)
        start, end = indexes
        msg = "For %s of page %s, expected %s but got %s. Paginator parameters were: %s"
        self.assertEqual(
            start,
            await page.astart_index(),
            msg % ("start index", page_num, start, await page.astart_index(), params),
        )
        self.assertEqual(
            end,
            await page.aend_index(),
            msg % ("end index", page_num, end, await page.aend_index(), params),
        )