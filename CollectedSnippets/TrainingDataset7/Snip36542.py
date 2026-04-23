def test_dict(self):
        # See ticket #18447
        lazydict = SimpleLazyObject(lambda: {"one": 1})
        self.assertEqual(lazydict["one"], 1)
        lazydict["one"] = -1
        self.assertEqual(lazydict["one"], -1)
        self.assertIn("one", lazydict)
        self.assertNotIn("two", lazydict)
        self.assertEqual(len(lazydict), 1)
        del lazydict["one"]
        with self.assertRaises(KeyError):
            lazydict["one"]