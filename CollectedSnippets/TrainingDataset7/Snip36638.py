def test_mark_safe_lazy_result_implements_dunder_html(self):
        self.assertEqual(mark_safe(lazystr("a&b")).__html__(), "a&b")