async def test_async_page_aiteration(self):
        paginator = AsyncPaginator(Article.objects.order_by("id"), 5)
        p = await paginator.apage(1)
        object_list = [obj async for obj in p]
        self.assertEqual(len(object_list), 5)