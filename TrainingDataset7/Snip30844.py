def test_ticket_21748_double_negated_and(self):
        i1 = Identifier.objects.create(name="i1")
        i2 = Identifier.objects.create(name="i2")
        Identifier.objects.create(name="i3")
        p1 = Program.objects.create(identifier=i1)
        c1 = Channel.objects.create(identifier=i1)
        Program.objects.create(identifier=i2)
        # Check the ~~Q() (or equivalently .exclude(~Q)) works like Q() for
        # join promotion.
        qs1_doubleneg = Identifier.objects.exclude(
            ~Q(program__id=p1.id, channel__id=c1.id)
        ).order_by("pk")
        qs1_filter = Identifier.objects.filter(
            program__id=p1.id, channel__id=c1.id
        ).order_by("pk")
        self.assertQuerySetEqual(qs1_doubleneg, qs1_filter, lambda x: x)
        self.assertEqual(
            str(qs1_filter.query).count("JOIN"), str(qs1_doubleneg.query).count("JOIN")
        )
        self.assertEqual(2, str(qs1_doubleneg.query).count("INNER JOIN"))
        self.assertEqual(
            str(qs1_filter.query).count("INNER JOIN"),
            str(qs1_doubleneg.query).count("INNER JOIN"),
        )