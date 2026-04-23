def test_last_page(self):
        paginator = Paginator(Article.objects.order_by("id"), 5)
        p = paginator.page(2)
        self.assertEqual("<Page 2 of 2>", str(p))
        self.assertSequenceEqual(p.object_list, self.articles[5:])
        self.assertFalse(p.has_next())
        self.assertTrue(p.has_previous())
        self.assertTrue(p.has_other_pages())
        with self.assertRaises(InvalidPage):
            p.next_page_number()
        self.assertEqual(1, p.previous_page_number())
        self.assertEqual(6, p.start_index())
        self.assertEqual(9, p.end_index())