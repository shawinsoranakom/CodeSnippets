def test_combine_negated_boolean_expression(self):
        tagged = Tag.objects.filter(category=OuterRef("pk"))
        tests = [
            Q() & ~Exists(tagged),
            Q() | ~Exists(tagged),
            Q() ^ ~Exists(tagged),
        ]
        for q in tests:
            with self.subTest(q=q):
                self.assertIsInstance(q, NegatedExpression)