def test_disjunction_promotion_select_related(self):
        fk1 = FK1.objects.create(f1="f1", f2="f2")
        basea = BaseA.objects.create(a=fk1)
        qs = BaseA.objects.filter(Q(a=fk1) | Q(b=2))
        self.assertEqual(str(qs.query).count(" JOIN "), 0)
        qs = qs.select_related("a", "b")
        self.assertEqual(str(qs.query).count(" INNER JOIN "), 0)
        self.assertEqual(str(qs.query).count(" LEFT OUTER JOIN "), 2)
        with self.assertNumQueries(1):
            self.assertSequenceEqual(qs, [basea])
            self.assertEqual(qs[0].a, fk1)
            self.assertIs(qs[0].b, None)