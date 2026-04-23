async def test_paginating_unordered_queryset_raises_warning_async(self):
        msg = (
            "Pagination may yield inconsistent results with an unordered "
            "object_list: <class 'pagination.models.Article'> QuerySet."
        )
        with self.assertWarnsMessage(UnorderedObjectListWarning, msg) as cm:
            AsyncPaginator(Article.objects.all(), 5)
        # The warning points at the BasePaginator caller.
        # The reason is that the UnorderedObjectListWarning occurs in
        # BasePaginator.
        base_paginator_path = pathlib.Path(inspect.getfile(BasePaginator))
        self.assertIn(
            cm.filename,
            [str(base_paginator_path), str(base_paginator_path.with_suffix(".py"))],
        )