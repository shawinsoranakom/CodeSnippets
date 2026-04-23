def test_queries_across_generic_relations(self):
        """
        Queries across generic relations respect the content types. Even though
        there are two TaggedItems with a tag of "fatty", this query only pulls
        out the one with the content type related to Animals.
        """
        self.assertSequenceEqual(
            Animal.objects.order_by("common_name"),
            [self.lion, self.platypus],
        )