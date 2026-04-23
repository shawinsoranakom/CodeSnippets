def test_correct_lookup(self):
        """
        When passing proxy model objects, child objects, or parent objects,
        lookups work fine.
        """
        out_a = [self.oa]
        out_b = [self.ob, self.pob1]
        out_c = [self.c]

        # proxy model objects
        self.assertSequenceEqual(
            ObjectB.objects.filter(objecta=self.poa).order_by("name"), out_b
        )
        self.assertSequenceEqual(
            ObjectA.objects.filter(objectb__in=self.pob).order_by("pk"), out_a * 2
        )

        # child objects
        self.assertSequenceEqual(ObjectB.objects.filter(objecta__in=[self.coa]), [])
        self.assertSequenceEqual(
            ObjectB.objects.filter(objecta__in=[self.poa, self.coa]).order_by("name"),
            out_b,
        )
        self.assertSequenceEqual(
            ObjectB.objects.filter(objecta__in=iter([self.poa, self.coa])).order_by(
                "name"
            ),
            out_b,
        )

        # parent objects
        self.assertSequenceEqual(ObjectC.objects.exclude(childobjecta=self.oa), out_c)

        # QuerySet related object type checking shouldn't issue queries
        # (the querysets aren't evaluated here, hence zero queries) (#23266).
        with self.assertNumQueries(0):
            ObjectB.objects.filter(objecta__in=ObjectA.objects.all())