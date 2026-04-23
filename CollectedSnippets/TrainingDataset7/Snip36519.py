def test_class(self):
        self.assertIsInstance(self.lazy_wrap(42), int)

        class Bar(Foo):
            pass

        self.assertIsInstance(self.lazy_wrap(Bar()), Foo)