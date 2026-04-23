async def test_page_sequence_async(self):
        eleven = "abcdefghijk"
        page2 = await AsyncPaginator(eleven, per_page=5, orphans=1).apage(2)
        await page2.aget_object_list()
        self.assertEqual(len(page2), 6)
        self.assertIn("k", page2)
        self.assertNotIn("a", page2)
        self.assertEqual("".join(page2), "fghijk")
        self.assertEqual("".join(reversed(page2)), "kjihgf")