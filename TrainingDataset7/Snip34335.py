def test_simple_tag_wrapped(self):
        @self.library.simple_tag
        @functools.lru_cache(maxsize=32)
        def func():
            return ""

        func_wrapped = self.library.tags["func"].__wrapped__
        self.assertIs(func_wrapped, func)
        self.assertTrue(hasattr(func_wrapped, "cache_info"))