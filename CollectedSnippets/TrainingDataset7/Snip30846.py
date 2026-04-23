def test_ticket_21748_complex_filter(self):
        i1 = Identifier.objects.create(name="i1")
        i2 = Identifier.objects.create(name="i2")
        Identifier.objects.create(name="i3")
        p1 = Program.objects.create(identifier=i1)
        c1 = Channel.objects.create(identifier=i1)
        p2 = Program.objects.create(identifier=i2)
        # Finally, a more complex case, one time in a way where each
        # NOT is pushed to lowest level in the boolean tree, and
        # another query where this isn't done.
        qs1 = Identifier.objects.filter(
            ~Q(~Q(program__id=p2.id, channel__id=c1.id) & Q(program__id=p1.id))
        ).order_by("pk")
        qs2 = Identifier.objects.filter(
            Q(Q(program__id=p2.id, channel__id=c1.id) | ~Q(program__id=p1.id))
        ).order_by("pk")
        self.assertQuerySetEqual(qs1, qs2, lambda x: x)
        self.assertEqual(str(qs1.query).count("JOIN"), str(qs2.query).count("JOIN"))
        self.assertEqual(0, str(qs1.query).count("INNER JOIN"))
        self.assertEqual(
            str(qs1.query).count("INNER JOIN"), str(qs2.query).count("INNER JOIN")
        )