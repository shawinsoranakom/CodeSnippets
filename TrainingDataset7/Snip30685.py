def test_join_already_in_query(self):
        # Ordering by model related to nullable relations should not change
        # the join type of already existing joins.
        Plaything.objects.create(name="p1")
        s = SingleObject.objects.create(name="s")
        r = RelatedObject.objects.create(single=s, f=1)
        p2 = Plaything.objects.create(name="p2", others=r)
        qs = Plaything.objects.filter(others__isnull=False).order_by("pk")
        self.assertNotIn("JOIN", str(qs.query))
        qs = Plaything.objects.filter(others__f__isnull=False).order_by("pk")
        self.assertIn("INNER", str(qs.query))
        qs = qs.order_by("others__single__name")
        # The ordering by others__single__pk will add one new join (to single)
        # and that join must be LEFT join. The already existing join to related
        # objects must be kept INNER. So, we have both an INNER and a LEFT join
        # in the query.
        self.assertEqual(str(qs.query).count("LEFT"), 1)
        self.assertEqual(str(qs.query).count("INNER"), 1)
        self.assertSequenceEqual(qs, [p2])