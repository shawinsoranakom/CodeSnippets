def test_getattr_falsey(self):
        class Thing:
            def __getattr__(self, key):
                return []

        obj = self.lazy_wrap(Thing())
        self.assertEqual(obj.main, [])