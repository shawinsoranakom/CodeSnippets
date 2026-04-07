async def test_aget_page_async(self):
        """
        AsyncPaginator.aget_page() returns a valid page even with invalid page
        arguments.
        """
        paginator = AsyncPaginator([1, 2, 3], 2)
        page = await paginator.aget_page(1)
        self.assertEqual(page.number, 1)
        self.assertEqual(page.object_list, [1, 2])
        # An empty page returns the last page.
        self.assertEqual((await paginator.aget_page(3)).number, 2)
        # Non-integer page returns the first page.
        self.assertEqual((await paginator.aget_page(None)).number, 1)