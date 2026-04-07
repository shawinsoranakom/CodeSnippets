def test_special_re_chars(self):
        def func1():
            warnings.warn("[.*x+]y?", UserWarning)

        with self.assertWarnsMessage(UserWarning, "[.*x+]y?"):
            func1()