def test_from_uuid_pk_lookup_uuid_pk_integer_pk(self):
        # From uuid-pk model, prefetch <uuid-pk model>.<integer-pk model>:
        with self.assertNumQueries(4):
            spooky = Pet.objects.prefetch_related(
                "fleas_hosted__current_room__house"
            ).get(name="Spooky")
        with self.assertNumQueries(0):
            self.assertEqual("Racoon", spooky.fleas_hosted.all()[0].current_room.name)