def test_generic_reverse_relation_with_mti(self):
        """
        Filtering with a reverse generic relation, where the GenericRelation
        comes from multi-table inheritance.
        """
        place = Place.objects.create(name="Test Place")
        link = Link.objects.create(content_object=place)
        result = Link.objects.filter(places=place)
        self.assertCountEqual(result, [link])