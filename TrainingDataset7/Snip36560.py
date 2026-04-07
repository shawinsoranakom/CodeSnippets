def test_negative_words(self):
        """words(n) returns n + 19 words, even if n is negative."""
        self.assertEqual(
            words(-5),
            "lorem ipsum dolor sit amet consectetur adipisicing elit sed do "
            "eiusmod tempor incididunt ut",
        )