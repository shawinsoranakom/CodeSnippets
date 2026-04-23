def test_text(self):
        obj = self.lazy_wrap("foo")
        self.assertEqual(str(obj), "foo")