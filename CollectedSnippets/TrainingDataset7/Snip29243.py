def test_reverse_relations(self):
        """
        Querying across reverse relations and then another relation should
        insert outer joins correctly so as not to exclude results.
        """
        obj = OuterA.objects.create()
        self.assertSequenceEqual(OuterA.objects.filter(inner__third=None), [obj])
        self.assertSequenceEqual(OuterA.objects.filter(inner__third__data=None), [obj])

        inner = Inner.objects.create(first=obj)
        self.assertSequenceEqual(
            Inner.objects.filter(first__inner__third=None), [inner]
        )

        # Ticket #13815: check if <reverse>_isnull=False does not produce
        # faulty empty lists
        outerb = OuterB.objects.create(data="reverse")
        self.assertSequenceEqual(OuterB.objects.filter(inner__isnull=False), [])
        Inner.objects.create(first=obj)
        self.assertSequenceEqual(OuterB.objects.exclude(inner__isnull=False), [outerb])