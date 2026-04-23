async def test_get_page_hook_async(self):
        """
        An AsyncPaginator subclass can use the ``_get_page`` hook to
        return an alternative to the standard AsyncPage class.
        """
        eleven = "abcdefghijk"
        paginator = AsyncValidAdjacentNumsPaginator(eleven, per_page=6)
        page1 = await paginator.apage(1)
        page2 = await paginator.apage(2)
        self.assertIsNone(await page1.aprevious_page_number())
        self.assertEqual(await page1.anext_page_number(), 2)
        self.assertEqual(await page2.aprevious_page_number(), 1)
        self.assertIsNone(await page2.anext_page_number())