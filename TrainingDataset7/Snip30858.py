def test_disjunction_promotion2(self):
        qs = BaseA.objects.filter(a__f1="foo")
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)
        # Now we have two different joins in an ORed condition, these
        # must be OUTER joins. The pre-existing join should remain INNER.
        qs = qs.filter(Q(b__f1="foo") | Q(c__f2="foo"))
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 2)
        # Reverse case.
        qs = BaseA.objects.filter(Q(b__f1="foo") | Q(c__f2="foo"))
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 2)
        qs = qs.filter(a__f1="foo")
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 2)