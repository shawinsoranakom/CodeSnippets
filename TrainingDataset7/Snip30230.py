def test_order(self):
        with self.assertNumQueries(4):
            # The following two queries must be done in the same order as
            # written, otherwise 'primary_house' will cause non-prefetched
            # lookups
            qs = Person.objects.prefetch_related(
                "houses__rooms", "primary_house__occupants"
            )
            [list(p.primary_house.occupants.all()) for p in qs]