def test_invalid_combinations(self):
        msg = "A Lexeme can only be combined with another Lexeme, got NoneType."
        with self.assertRaisesMessage(TypeError, msg):
            Line.objects.filter(dialogue__search=None | Lexeme("kneecaps"))

        with self.assertRaisesMessage(TypeError, msg):
            Line.objects.filter(dialogue__search=None & Lexeme("kneecaps"))