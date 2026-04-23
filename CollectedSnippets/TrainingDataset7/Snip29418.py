async def test_aget_page_empty_object_list_async(self):
        """AsyncPaginator.aget_page() with an empty object_list."""
        paginator = AsyncPaginator([], 2)
        # An empty page returns the last page.
        self.assertEqual((await paginator.aget_page(1)).number, 1)
        self.assertEqual((await paginator.aget_page(2)).number, 1)
        # Non-integer page returns the first page.
        self.assertEqual((await paginator.aget_page(None)).number, 1)