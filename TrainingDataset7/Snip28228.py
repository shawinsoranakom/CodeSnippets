def test_lazy_strings_not_evaluated(self):
        lazy_func = lazy(lambda x: 0 / 0, int)  # raises ZeroDivisionError if evaluated.
        f = models.CharField(choices=[(lazy_func("group"), [("a", "A"), ("b", "B")])])
        self.assertEqual(f.get_choices(include_blank=True)[0], ("", "---------"))