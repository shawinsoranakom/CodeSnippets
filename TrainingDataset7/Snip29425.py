async def test_aget_elided_page_range_async(self):
        # AsyncPaginator.avalidate_number() must be called:
        paginator = AsyncPaginator([1, 2, 3], 2)
        with unittest.mock.patch.object(paginator, "avalidate_number") as mock:
            mock.assert_not_called()
            [p async for p in paginator.aget_elided_page_range(2)]
            mock.assert_called_with(2)

        ELLIPSIS = Paginator.ELLIPSIS

        # Range is not elided if not enough pages when using default arguments:
        paginator = AsyncPaginator(range(10 * 100), 100)
        page_range = paginator.aget_elided_page_range(1)
        self.assertIsInstance(page_range, collections.abc.AsyncGenerator)
        self.assertNotIn(ELLIPSIS, [p async for p in page_range])
        paginator = AsyncPaginator(range(10 * 100 + 1), 100)
        self.assertIsInstance(page_range, collections.abc.AsyncGenerator)
        page_range = paginator.aget_elided_page_range(1)
        self.assertIn(ELLIPSIS, [p async for p in page_range])

        # Range should be elided if enough pages when using default arguments:
        tests = [
            # on_each_side=3, on_ends=2
            (1, [1, 2, 3, 4, ELLIPSIS, 49, 50]),
            (6, [1, 2, 3, 4, 5, 6, 7, 8, 9, ELLIPSIS, 49, 50]),
            (7, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, ELLIPSIS, 49, 50]),
            (8, [1, 2, ELLIPSIS, 5, 6, 7, 8, 9, 10, 11, ELLIPSIS, 49, 50]),
            (43, [1, 2, ELLIPSIS, 40, 41, 42, 43, 44, 45, 46, ELLIPSIS, 49, 50]),
            (44, [1, 2, ELLIPSIS, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50]),
            (45, [1, 2, ELLIPSIS, 42, 43, 44, 45, 46, 47, 48, 49, 50]),
            (50, [1, 2, ELLIPSIS, 47, 48, 49, 50]),
        ]
        paginator = AsyncPaginator(range(5000), 100)
        for number, expected in tests:
            with self.subTest(number=number):
                page_range = paginator.aget_elided_page_range(number)
                self.assertIsInstance(page_range, collections.abc.AsyncGenerator)
                self.assertEqual([p async for p in page_range], expected)

        # Range is not elided if not enough pages when using custom arguments:
        tests = [
            (6, 2, 1, 1),
            (8, 1, 3, 1),
            (8, 4, 0, 1),
            (4, 1, 1, 1),
            # When on_each_side and on_ends are both <= 1 but not both == 1 it
            # is a special case where the range is not elided until an extra
            # page is added.
            (2, 0, 1, 2),
            (2, 1, 0, 2),
            (1, 0, 0, 2),
        ]
        for pages, on_each_side, on_ends, elided_after in tests:
            for offset in range(elided_after + 1):
                with self.subTest(
                    pages=pages,
                    offset=elided_after,
                    on_each_side=on_each_side,
                    on_ends=on_ends,
                ):
                    paginator = AsyncPaginator(range((pages + offset) * 100), 100)
                    page_range = paginator.aget_elided_page_range(
                        1,
                        on_each_side=on_each_side,
                        on_ends=on_ends,
                    )
                    self.assertIsInstance(page_range, collections.abc.AsyncGenerator)
                    page_list = [p async for p in page_range]
                    if offset < elided_after:
                        self.assertNotIn(ELLIPSIS, page_list)
                    else:
                        self.assertIn(ELLIPSIS, page_list)

        # Range should be elided if enough pages when using custom arguments:
        tests = self.get_test_cases_for_test_get_elided_page_range()
        paginator = AsyncPaginator(range(5000), 100)
        for number, on_each_side, on_ends, expected in tests:
            with self.subTest(
                number=number, on_each_side=on_each_side, on_ends=on_ends
            ):
                page_range = paginator.aget_elided_page_range(
                    number,
                    on_each_side=on_each_side,
                    on_ends=on_ends,
                )
                self.assertIsInstance(page_range, collections.abc.AsyncGenerator)
                self.assertEqual([p async for p in page_range], expected)