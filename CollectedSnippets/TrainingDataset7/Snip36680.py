def test_get_text_list(self):
        self.assertEqual(text.get_text_list(["a", "b", "c", "d"]), "a, b, c or d")
        self.assertEqual(text.get_text_list(["a", "b", "c"], "and"), "a, b and c")
        self.assertEqual(text.get_text_list(["a", "b"], "and"), "a and b")
        self.assertEqual(text.get_text_list(["a"]), "a")
        self.assertEqual(text.get_text_list([]), "")
        with override("ar"):
            self.assertEqual(text.get_text_list(["a", "b", "c"]), "a، b أو c")