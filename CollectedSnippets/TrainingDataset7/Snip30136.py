def test_prefetch_related_from_uuid_model_to_uuid_model(self):
        fleas = [Flea.objects.create() for i in range(3)]
        Pet.objects.create(name="Fifi").fleas_hosted.add(*fleas)
        Pet.objects.create(name="Bobo").fleas_hosted.add(*fleas)

        with self.assertNumQueries(2):
            pet = Pet.objects.prefetch_related("fleas_hosted").get(name="Fifi")
        with self.assertNumQueries(0):
            self.assertEqual(3, len(pet.fleas_hosted.all()))

        with self.assertNumQueries(2):
            flea = Flea.objects.prefetch_related("pets_visited").get(pk=fleas[0].pk)
        with self.assertNumQueries(0):
            self.assertEqual(2, len(flea.pets_visited.all()))