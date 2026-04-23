async def test_aget_object_list(self):
        paginator = AsyncPaginator(Article.objects.order_by("id"), 5)
        p = await paginator.apage(1)

        # object_list queryset is converted to list.
        first_called_objs = await p.aget_object_list()
        self.assertIsInstance(first_called_objs, list)
        # It returns the same list that was converted on the first call.
        second_called_objs = await p.aget_object_list()
        self.assertEqual(id(first_called_objs), id(second_called_objs))