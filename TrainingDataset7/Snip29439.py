async def test_async_page_object_list_raises_type_error_before_await(self):
        paginator = AsyncPaginator(Article.objects.order_by("id"), 5)
        p = await paginator.apage(1)

        with self.subTest(func="len"):
            msg = "AsyncPage.aget_object_list() must be awaited before calling len()."
            with self.assertRaisesMessage(TypeError, msg):
                len(p)

        with self.subTest(func="reversed"):
            msg = (
                "AsyncPage.aget_object_list() must be awaited before calling "
                "reversed()."
            )
            with self.assertRaisesMessage(TypeError, msg):
                reversed(p)

        with self.subTest(func="index"):
            msg = "AsyncPage.aget_object_list() must be awaited before using indexing."
            with self.assertRaisesMessage(TypeError, msg):
                p[0]