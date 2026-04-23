def test_q_repr(self):
        or_expr = Q(baz=Article(headline="Foö"))
        self.assertEqual(repr(or_expr), "<Q: (AND: ('baz', <Article: Foö>))>")
        negated_or = ~Q(baz=Article(headline="Foö"))
        self.assertEqual(repr(negated_or), "<Q: (NOT (AND: ('baz', <Article: Foö>)))>")