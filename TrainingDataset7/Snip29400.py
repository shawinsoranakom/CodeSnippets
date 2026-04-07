async def test_paginate_misc_classes_async(self):
        class CountContainer:
            async def acount(self):
                return 42

        # AsyncPaginator can be passed other objects with an acount() method.
        paginator = AsyncPaginator(CountContainer(), 10)
        self.assertEqual(42, await paginator.acount())
        self.assertEqual(5, await paginator.anum_pages())
        self.assertEqual([1, 2, 3, 4, 5], list(await paginator.apage_range()))

        # AsyncPaginator can be passed other objects that implement __len__.
        class LenContainer:
            def __len__(self):
                return 42

        paginator = AsyncPaginator(LenContainer(), 10)
        self.assertEqual(42, await paginator.acount())
        self.assertEqual(5, await paginator.anum_pages())
        self.assertEqual([1, 2, 3, 4, 5], list(await paginator.apage_range()))