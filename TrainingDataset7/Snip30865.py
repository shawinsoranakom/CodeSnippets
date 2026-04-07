def test_disjunction_promotion7(self):
        qs = BaseA.objects.filter(Q(a=1) | Q(a=2))
        self.assertEqual(str(qs.query).count("JOIN"), 0)
        qs = BaseA.objects.filter(Q(a__f1="foo") | (Q(b__f1="foo") & Q(a__f1="bar")))
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 1)
        qs = BaseA.objects.filter(
            (Q(a__f1="foo") | Q(b__f1="foo")) & (Q(a__f1="bar") | Q(c__f1="foo"))
        )
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 3)
        self.assertEqual(str(qs.query).count("INNER JOIN"), 0)
        qs = BaseA.objects.filter(
            Q(a__f1="foo") | Q(a__f1="bar") & (Q(b__f1="bar") | Q(c__f1="foo"))
        )
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 2)
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)