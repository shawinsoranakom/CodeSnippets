def test_special_re_chars(self):
        """assertRaisesMessage shouldn't interpret RE special chars."""

        def func1():
            raise ValueError("[.*x+]y?")

        with self.assertRaisesMessage(ValueError, "[.*x+]y?"):
            func1()