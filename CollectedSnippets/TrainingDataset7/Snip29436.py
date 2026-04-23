async def test_paginating_empty_queryset_does_not_warn_async(self):
        with warnings.catch_warnings(record=True) as recorded:
            AsyncPaginator(Article.objects.none(), 5)
        self.assertEqual(len(recorded), 0)