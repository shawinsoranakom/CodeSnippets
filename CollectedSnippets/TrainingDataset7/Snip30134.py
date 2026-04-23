def test_prefetch_related_from_uuid_model(self):
        Pet.objects.create(name="Fifi").people.add(
            Person.objects.create(name="Ellen"),
            Person.objects.create(name="George"),
        )

        with self.assertNumQueries(2):
            pet = Pet.objects.prefetch_related("people").get(name="Fifi")
        with self.assertNumQueries(0):
            self.assertEqual(2, len(pet.people.all()))