def test_smart_str(self):
        class Test:
            def __str__(self):
                return "ŠĐĆŽćžšđ"

        lazy_func = gettext_lazy("x")
        self.assertIs(smart_str(lazy_func), lazy_func)
        self.assertEqual(
            smart_str(Test()), "\u0160\u0110\u0106\u017d\u0107\u017e\u0161\u0111"
        )
        self.assertEqual(smart_str(1), "1")
        self.assertEqual(smart_str("foo"), "foo")