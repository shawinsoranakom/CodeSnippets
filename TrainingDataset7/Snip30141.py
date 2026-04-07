def test_from_integer_pk_lookup_uuid_pk_integer_pk(self):
        # From integer-pk model, prefetch <uuid-pk model>.<integer-pk model>:
        with self.assertNumQueries(3):
            racoon = Room.objects.prefetch_related("fleas__people_visited").get(
                name="Racoon"
            )
        with self.assertNumQueries(0):
            self.assertEqual("Bob", racoon.fleas.all()[0].people_visited.all()[0].name)