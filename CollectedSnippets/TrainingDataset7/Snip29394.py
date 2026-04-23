async def test_invalid_apage_number_async(self):
        """See test_invalid_page_number."""
        paginator = AsyncPaginator([1, 2, 3], 2)
        with self.assertRaises(InvalidPage):
            await paginator.apage(3)