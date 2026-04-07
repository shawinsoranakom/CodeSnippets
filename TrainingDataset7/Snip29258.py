def test_reverse_relationship_cache_cascade(self):
        """
        Regression test for #9023: accessing the reverse relationship shouldn't
        result in a cascading delete().
        """
        bar = UndergroundBar.objects.create(place=self.p1, serves_cocktails=False)

        # The bug in #9023: if you access the one-to-one relation *before*
        # setting to None and deleting, the cascade happens anyway.
        self.p1.undergroundbar
        bar.place.name = "foo"
        bar.place = None
        bar.save()
        self.p1.delete()

        self.assertEqual(Place.objects.count(), 1)
        self.assertEqual(UndergroundBar.objects.count(), 1)