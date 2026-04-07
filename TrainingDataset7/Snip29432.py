async def test_page_getitem_async(self):
        paginator = AsyncPaginator(Article.objects.order_by("id"), 5)
        p = await paginator.apage(1)

        msg = "AsyncPage indices must be integers or slices, not str."
        with self.assertRaisesMessage(TypeError, msg):
            p["has_previous"]

        self.assertIsNone(p.object_list._result_cache)

        self.assertNotIsInstance(p.object_list, list)

        await p.aget_object_list()

        self.assertEqual(p[0], self.articles[0])
        self.assertSequenceEqual(p[slice(2)], self.articles[:2])
        self.assertIsInstance(p.object_list, list)