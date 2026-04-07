def test_dir(self):
        obj = self.lazy_wrap("foo")
        self.assertEqual(dir(obj), dir("foo"))