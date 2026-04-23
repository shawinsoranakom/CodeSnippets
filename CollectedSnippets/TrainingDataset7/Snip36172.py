def test_copy(self):
        for copy_func in [copy.copy, lambda d: d.copy()]:
            with self.subTest(copy_func):
                d1 = MultiValueDict({"developers": ["Carl", "Fred"]})
                self.assertEqual(d1["developers"], "Fred")
                d2 = copy_func(d1)
                d2.update({"developers": "Groucho"})
                self.assertEqual(d2["developers"], "Groucho")
                self.assertEqual(d1["developers"], "Fred")

                d1 = MultiValueDict({"key": [[]]})
                self.assertEqual(d1["key"], [])
                d2 = copy_func(d1)
                d2["key"].append("Penguin")
                self.assertEqual(d1["key"], ["Penguin"])
                self.assertEqual(d2["key"], ["Penguin"])