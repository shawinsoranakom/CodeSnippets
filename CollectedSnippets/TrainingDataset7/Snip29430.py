async def test_last_page_async(self):
        paginator = AsyncPaginator(Article.objects.order_by("id"), 5)
        p = await paginator.apage(2)
        self.assertEqual("<Async Page 2>", str(p))
        object_list = await p.aget_object_list()
        self.assertSequenceEqual(object_list, self.articles[5:])
        self.assertFalse(await p.ahas_next())
        self.assertTrue(await p.ahas_previous())
        self.assertTrue(await p.ahas_other_pages())
        with self.assertRaises(InvalidPage):
            await p.anext_page_number()
        self.assertEqual(1, await p.aprevious_page_number())
        self.assertEqual(6, await p.astart_index())
        self.assertEqual(9, await p.aend_index())