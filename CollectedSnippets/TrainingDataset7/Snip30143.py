def test_from_integer_pk_lookup_integer_pk_uuid_pk_uuid_pk(self):
        # From integer-pk model, prefetch
        # <integer-pk model>.<uuid-pk model>.<uuid-pk model>:
        with self.assertNumQueries(4):
            redwood = House.objects.prefetch_related("rooms__fleas__pets_visited").get(
                name="Redwood"
            )
        with self.assertNumQueries(0):
            self.assertEqual(
                "Spooky",
                redwood.rooms.all()[0].fleas.all()[0].pets_visited.all()[0].name,
            )