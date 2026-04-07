def test_disjunction_promotion3(self):
        qs = BaseA.objects.filter(a__f2="bar")
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)
        # The ANDed a__f2 filter allows us to use keep using INNER JOIN
        # even inside the ORed case. If the join to a__ returns nothing,
        # the ANDed filter for a__f2 can't be true.
        qs = qs.filter(Q(a__f1="foo") | Q(b__f2="foo"))
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)
        self.assertEqual(str(qs.query).count("LEFT OUTER JOIN"), 1)