def test_annotate(self):
        hs1 = HasLinkThing.objects.create()
        hs2 = HasLinkThing.objects.create()
        HasLinkThing.objects.create()
        b = Board.objects.create(name=str(hs1.pk))
        Link.objects.create(content_object=hs2)
        link = Link.objects.create(content_object=hs1)
        Link.objects.create(content_object=b)
        qs = HasLinkThing.objects.annotate(Sum("links")).filter(pk=hs1.pk)
        # If content_type restriction isn't in the query's join condition,
        # then wrong results are produced here as the link to b will also match
        # (b and hs1 have equal pks).
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs[0].links__sum, link.id)
        link.delete()
        # Now if we don't have proper left join, we will not produce any
        # results at all here.
        # clear cached results
        qs = qs.all()
        self.assertEqual(qs.count(), 1)
        # Note - 0 here would be a nicer result...
        self.assertIs(qs[0].links__sum, None)
        # Finally test that filtering works.
        self.assertEqual(qs.filter(links__sum__isnull=True).count(), 1)
        self.assertEqual(qs.filter(links__sum__isnull=False).count(), 0)