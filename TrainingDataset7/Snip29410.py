def test_page_sequence(self):
        """
        A paginator page acts like a standard sequence.
        """
        eleven = "abcdefghijk"
        page2 = Paginator(eleven, per_page=5, orphans=1).page(2)
        self.assertEqual(len(page2), 6)
        self.assertIn("k", page2)
        self.assertNotIn("a", page2)
        self.assertEqual("".join(page2), "fghijk")
        self.assertEqual("".join(reversed(page2)), "kjihgf")