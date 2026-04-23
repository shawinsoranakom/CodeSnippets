def test_bytes(self):
        obj = self.lazy_wrap(b"foo")
        self.assertEqual(bytes(obj), b"foo")