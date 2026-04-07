def test_word_with_dot(self):
        self.assertEqual(urlize("some.organization"), "some.organization")