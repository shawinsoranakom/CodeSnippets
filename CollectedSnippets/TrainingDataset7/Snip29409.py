async def test_page_indexes_async(self):
        """See test_page_indexes"""
        tests = self.get_test_cases_for_test_page_indexes()
        for params, first, last in tests:
            await self.check_indexes_async(params, "first", first)
            await self.check_indexes_async(params, "last", last)

        # When no items and no empty first page, we should get EmptyPage error.
        with self.assertRaises(EmptyPage):
            await self.check_indexes_async(([], 4, 0, False), 1, None)
        with self.assertRaises(EmptyPage):
            await self.check_indexes_async(([], 4, 1, False), 1, None)
        with self.assertRaises(EmptyPage):
            await self.check_indexes_async(([], 4, 2, False), 1, None)