def test_dictwrapper(self):
        def f(x):
            return "*%s" % x

        d = DictWrapper({"a": "a"}, f, "xx_")
        self.assertEqual(
            "Normal: %(a)s. Modified: %(xx_a)s" % d, "Normal: a. Modified: *a"
        )