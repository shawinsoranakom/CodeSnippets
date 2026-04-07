def test_disjunction_promotion4(self):
        qs = BaseA.objects.filter(a__f1="foo")
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)
        qs = qs.filter(Q(a=1) | Q(a=2))
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)