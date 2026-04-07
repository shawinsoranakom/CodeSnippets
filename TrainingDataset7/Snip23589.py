def test_ticket_20378(self):
        # Create a couple of extra HasLinkThing so that the autopk value
        # isn't the same for Link and HasLinkThing.
        hs1 = HasLinkThing.objects.create()
        hs2 = HasLinkThing.objects.create()
        hs3 = HasLinkThing.objects.create()
        hs4 = HasLinkThing.objects.create()
        l1 = Link.objects.create(content_object=hs3)
        l2 = Link.objects.create(content_object=hs4)
        self.assertSequenceEqual(HasLinkThing.objects.filter(links=l1), [hs3])
        self.assertSequenceEqual(HasLinkThing.objects.filter(links=l2), [hs4])
        self.assertSequenceEqual(
            HasLinkThing.objects.exclude(links=l2), [hs1, hs2, hs3]
        )
        self.assertSequenceEqual(
            HasLinkThing.objects.exclude(links=l1), [hs1, hs2, hs4]
        )