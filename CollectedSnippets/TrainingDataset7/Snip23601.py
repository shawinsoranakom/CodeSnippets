def test_generic_reverse_relation_exclude_filter(self):
        place1 = Place.objects.create(name="Test Place 1")
        place2 = Place.objects.create(name="Test Place 2")
        Link.objects.create(content_object=place1)
        link2 = Link.objects.create(content_object=place2)
        qs = Link.objects.filter(~Q(places__name="Test Place 1"))
        self.assertSequenceEqual(qs, [link2])
        qs = Link.objects.exclude(places__name="Test Place 1")
        self.assertSequenceEqual(qs, [link2])