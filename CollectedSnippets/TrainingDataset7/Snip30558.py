def test_repr(self):
        self.assertEqual(
            repr(JoinPromoter(AND, 3, True)),
            "JoinPromoter(connector='AND', num_children=3, negated=True)",
        )