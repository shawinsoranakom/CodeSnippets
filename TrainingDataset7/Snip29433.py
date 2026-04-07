def test_paginating_unordered_queryset_raises_warning(self):
        msg = (
            "Pagination may yield inconsistent results with an unordered "
            "object_list: <class 'pagination.models.Article'> QuerySet."
        )
        with self.assertWarnsMessage(UnorderedObjectListWarning, msg) as cm:
            Paginator(Article.objects.all(), 5)
        # The warning points at the Paginator caller (i.e. the stacklevel
        # is appropriate).
        self.assertEqual(cm.filename, __file__)