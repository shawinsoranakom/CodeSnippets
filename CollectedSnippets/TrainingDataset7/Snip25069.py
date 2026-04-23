def test_ngettext_lazy_bool(self):
        self.assertTrue(ngettext_lazy("%d good result", "%d good results"))
        self.assertFalse(ngettext_lazy("", ""))