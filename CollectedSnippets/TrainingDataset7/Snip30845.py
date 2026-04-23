def test_ticket_21748_double_negated_or(self):
        i1 = Identifier.objects.create(name="i1")
        i2 = Identifier.objects.create(name="i2")
        Identifier.objects.create(name="i3")
        p1 = Program.objects.create(identifier=i1)
        c1 = Channel.objects.create(identifier=i1)
        p2 = Program.objects.create(identifier=i2)
        # Test OR + doubleneg. The expected result is that channel is LOUTER
        # joined, program INNER joined
        qs1_filter = Identifier.objects.filter(
            Q(program__id=p2.id, channel__id=c1.id) | Q(program__id=p1.id)
        ).order_by("pk")
        qs1_doubleneg = Identifier.objects.exclude(
            ~Q(Q(program__id=p2.id, channel__id=c1.id) | Q(program__id=p1.id))
        ).order_by("pk")
        self.assertQuerySetEqual(qs1_doubleneg, qs1_filter, lambda x: x)
        self.assertEqual(
            str(qs1_filter.query).count("JOIN"), str(qs1_doubleneg.query).count("JOIN")
        )
        self.assertEqual(1, str(qs1_doubleneg.query).count("INNER JOIN"))
        self.assertEqual(
            str(qs1_filter.query).count("INNER JOIN"),
            str(qs1_doubleneg.query).count("INNER JOIN"),
        )