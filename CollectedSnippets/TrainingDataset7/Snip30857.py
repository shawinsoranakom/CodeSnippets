def test_disjunction_promotion1(self):
        # Pre-existing join, add two ORed filters to the same join,
        # all joins can be INNER JOINS.
        qs = BaseA.objects.filter(a__f1="foo")
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)
        qs = qs.filter(Q(b__f1="foo") | Q(b__f2="foo"))
        self.assertEqual(str(qs.query).count("INNER JOIN"), 2)
        # Reverse the order of AND and OR filters.
        qs = BaseA.objects.filter(Q(b__f1="foo") | Q(b__f2="foo"))
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)
        qs = qs.filter(a__f1="foo")
        self.assertEqual(str(qs.query).count("INNER JOIN"), 2)