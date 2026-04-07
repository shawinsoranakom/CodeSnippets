def test_11_sorting(self):
        "Sorting"
        pl, ul = self.lists_of_len()
        pl.insert(0, pl.pop())
        ul.insert(0, ul.pop())
        pl.sort()
        ul.sort()
        self.assertEqual(pl[:], ul[:], "sort")
        mid = pl[len(pl) // 2]
        pl.sort(key=lambda x: (mid - x) ** 2)
        ul.sort(key=lambda x: (mid - x) ** 2)
        self.assertEqual(pl[:], ul[:], "sort w/ key")

        pl.insert(0, pl.pop())
        ul.insert(0, ul.pop())
        pl.sort(reverse=True)
        ul.sort(reverse=True)
        self.assertEqual(pl[:], ul[:], "sort w/ reverse")
        mid = pl[len(pl) // 2]
        pl.sort(key=lambda x: (mid - x) ** 2)
        ul.sort(key=lambda x: (mid - x) ** 2)
        self.assertEqual(pl[:], ul[:], "sort w/ key")