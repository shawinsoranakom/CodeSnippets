async def test_paginator_iteration_async(self):
        paginator = AsyncPaginator([1, 2, 3], 2)
        page_iterator = aiter(paginator)
        for page, expected in enumerate(([1, 2], [3]), start=1):
            with self.subTest(page=page):
                async_page = await anext(page_iterator)
                self.assertEqual(expected, [obj async for obj in async_page])
        self.assertEqual(
            [str(page) async for page in aiter(paginator)],
            ["<Async Page 1>", "<Async Page 2>"],
        )