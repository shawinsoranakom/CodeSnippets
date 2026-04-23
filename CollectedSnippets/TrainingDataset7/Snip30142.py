def test_from_integer_pk_lookup_integer_pk_uuid_pk(self):
        # From integer-pk model, prefetch <integer-pk model>.<uuid-pk model>:
        with self.assertNumQueries(3):
            redwood = House.objects.prefetch_related("rooms__fleas").get(name="Redwood")
        with self.assertNumQueries(0):
            self.assertEqual(3, len(redwood.rooms.all()[0].fleas.all()))