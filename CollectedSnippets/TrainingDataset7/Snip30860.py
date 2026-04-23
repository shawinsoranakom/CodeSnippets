def test_disjunction_promotion3_demote(self):
        # This one needs demotion logic: the first filter causes a to be
        # outer joined, the second filter makes it inner join again.
        qs = BaseA.objects.filter(Q(a__f1="foo") | Q(b__f2="foo")).filter(a__f2="bar")
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 1)