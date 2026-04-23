def test_from_uuid_pk_lookup_integer_pk2_uuid_pk2(self):
        # From uuid-pk model, prefetch
        # <integer-pk model>.<integer-pk model>.<uuid-pk model>.<uuid-pk
        # model>:
        with self.assertNumQueries(5):
            spooky = Pet.objects.prefetch_related("people__houses__rooms__fleas").get(
                name="Spooky"
            )
        with self.assertNumQueries(0):
            self.assertEqual(
                3,
                len(spooky.people.all()[0].houses.all()[0].rooms.all()[0].fleas.all()),
            )