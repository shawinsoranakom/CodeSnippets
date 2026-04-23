def test_ticket_21748(self):
        i1 = Identifier.objects.create(name="i1")
        i2 = Identifier.objects.create(name="i2")
        i3 = Identifier.objects.create(name="i3")
        Program.objects.create(identifier=i1)
        Channel.objects.create(identifier=i1)
        Program.objects.create(identifier=i2)
        self.assertSequenceEqual(
            Identifier.objects.filter(program=None, channel=None), [i3]
        )
        self.assertSequenceEqual(
            Identifier.objects.exclude(program=None, channel=None).order_by("name"),
            [i1, i2],
        )