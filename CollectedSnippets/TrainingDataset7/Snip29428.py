async def test_first_page_async(self):
        paginator = AsyncPaginator(Article.objects.order_by("id"), 5)
        p = await paginator.apage(1)
        self.assertEqual("<Async Page 1>", str(p))
        object_list = await p.aget_object_list()
        self.assertSequenceEqual(object_list, self.articles[:5])
        self.assertTrue(await p.ahas_next())
        self.assertFalse(await p.ahas_previous())
        self.assertTrue(await p.ahas_other_pages())
        self.assertEqual(2, await p.anext_page_number())
        with self.assertRaises(InvalidPage):
            await p.aprevious_page_number()
        self.assertEqual(1, await p.astart_index())
        self.assertEqual(5, await p.aend_index())