def test_disjunction_promotion4_demote(self):
        qs = BaseA.objects.filter(Q(a=1) | Q(a=2))
        self.assertEqual(str(qs.query).count("JOIN"), 0)
        # Demote needed for the "a" join. It is marked as outer join by
        # above filter (even if it is trimmed away).
        qs = qs.filter(a__f1="foo")
        self.assertEqual(str(qs.query).count("INNER JOIN"), 1)