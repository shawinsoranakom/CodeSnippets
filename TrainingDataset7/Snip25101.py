def test_get_format_lazy_format(self):
        self.assertEqual(get_format(gettext_lazy("DATE_FORMAT")), "N j, Y")