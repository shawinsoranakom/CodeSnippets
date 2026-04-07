def test_paginator_iteration(self):
        paginator = Paginator([1, 2, 3], 2)
        page_iterator = iter(paginator)
        for page, expected in enumerate(([1, 2], [3]), start=1):
            with self.subTest(page=page):
                self.assertEqual(expected, list(next(page_iterator)))

        self.assertEqual(
            [str(page) for page in iter(paginator)],
            ["<Page 1 of 2>", "<Page 2 of 2>"],
        )