def test_disjunction_promotion6(self):
        qs = BaseA.objects.filter(Q(a=1) | Q(a=2))
        self.assertEqual(str(qs.query).count("JOIN"), 0)
        qs = BaseA.objects.filter(Q(a__f1="foo") & Q(b__f1="foo"))
        self.assertEqual(str(qs.query).count("INNER JOIN"), 2)
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 0)

        qs = BaseA.objects.filter(Q(a__f1="foo") & Q(b__f1="foo"))
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 0)
        self.assertEqual(str(qs.query).count("INNER JOIN"), 2)
        qs = qs.filter(Q(a=1) | Q(a=2))
        self.assertEqual(str(qs.query).count("INNER JOIN"), 2)
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 0)