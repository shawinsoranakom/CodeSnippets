def test_disjunction_promotion_fexpression(self):
        qs = BaseA.objects.filter(Q(a__f1=F("b__f1")) | Q(b__f1="foo"))
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 1)
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)
        qs = BaseA.objects.filter(Q(a__f1=F("c__f1")) | Q(b__f1="foo"))
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 3)
        qs = BaseA.objects.filter(
            Q(a__f1=F("b__f1")) | Q(a__f2=F("b__f2")) | Q(c__f1="foo")
        )
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 3)
        qs = BaseA.objects.filter(Q(a__f1=F("c__f1")) | (Q(pk=1) & Q(pk=2)))
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 2)
        self.assertEqual(str(qs.query).count("INNER JOIN"), 0)