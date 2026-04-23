def test_generic_relation_ordering(self):
        """
        Ordering over a generic relation does not include extraneous
        duplicate results, nor excludes rows not participating in the relation.
        """
        p1 = Place.objects.create(name="South Park")
        p2 = Place.objects.create(name="The City")
        c = Company.objects.create(name="Chubby's Intl.")
        Link.objects.create(content_object=p1)
        Link.objects.create(content_object=c)

        places = list(Place.objects.order_by("links__id"))

        def count_places(place):
            return len([p for p in places if p.id == place.id])

        self.assertEqual(len(places), 2)
        self.assertEqual(count_places(p1), 1)
        self.assertEqual(count_places(p2), 1)