def test_mark_safe_result_implements_dunder_html(self):
        self.assertEqual(mark_safe("a&b").__html__(), "a&b")