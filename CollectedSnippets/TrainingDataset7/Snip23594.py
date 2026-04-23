def test_filter_targets_related_pk(self):
        # Use hardcoded PKs to ensure different PKs for "link" and "hs2"
        # objects.
        HasLinkThing.objects.create(pk=1)
        hs2 = HasLinkThing.objects.create(pk=2)
        link = Link.objects.create(content_object=hs2, pk=1)
        self.assertNotEqual(link.object_id, link.pk)
        self.assertSequenceEqual(HasLinkThing.objects.filter(links=link.pk), [hs2])