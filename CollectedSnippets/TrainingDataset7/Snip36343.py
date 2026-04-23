def test_lazy_mod_str(self):
        lazy_a = lazy(lambda: "a%s", str)
        lazy_b = lazy(lambda: "b", str)
        self.assertEqual("a%s" % lazy_b(), "ab")
        self.assertEqual(lazy_a() % "b", "ab")
        self.assertEqual(lazy_a() % lazy_b(), "ab")