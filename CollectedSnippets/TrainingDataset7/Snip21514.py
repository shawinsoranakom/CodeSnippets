def test_functions(self):
        self.assertEqual(repr(Coalesce("a", "b")), "Coalesce(F(a), F(b))")
        self.assertEqual(repr(Concat("a", "b")), "Concat(ConcatPair(F(a), F(b)))")
        self.assertEqual(repr(Length("a")), "Length(F(a))")
        self.assertEqual(repr(Lower("a")), "Lower(F(a))")
        self.assertEqual(repr(Substr("a", 1, 3)), "Substr(F(a), Value(1), Value(3))")
        self.assertEqual(repr(Upper("a")), "Upper(F(a))")