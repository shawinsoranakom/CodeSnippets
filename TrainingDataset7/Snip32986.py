def test_safestring(self):
        self.assertEqual(length(mark_safe("1234")), 4)