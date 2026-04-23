def test_conditional_escape(self):
        s = "<h1>interop</h1>"
        self.assertEqual(conditional_escape(s), "&lt;h1&gt;interop&lt;/h1&gt;")
        self.assertEqual(conditional_escape(mark_safe(s)), s)
        self.assertEqual(conditional_escape(lazystr(mark_safe(s))), s)