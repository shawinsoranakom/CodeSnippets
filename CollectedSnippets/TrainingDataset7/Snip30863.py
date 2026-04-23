def test_disjunction_promotion5_demote(self):
        qs = BaseA.objects.filter(Q(a=1) | Q(a=2))
        # Note that the above filters on a force the join to an
        # inner join even if it is trimmed.
        self.assertEqual(str(qs.query).count("JOIN"), 0)
        qs = qs.filter(Q(a__f1="foo") | Q(b__f1="foo"))
        # So, now the a__f1 join doesn't need promotion.
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)
        # But b__f1 does.
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 1)
        qs = BaseA.objects.filter(Q(a__f1="foo") | Q(b__f1="foo"))
        # Now the join to a is created as LOUTER
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 2)
        qs = qs.filter(Q(a=1) | Q(a=2))
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 1)