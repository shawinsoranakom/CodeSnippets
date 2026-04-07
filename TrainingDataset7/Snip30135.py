def test_prefetch_related_to_uuid_model(self):
        Person.objects.create(name="Bella").pets.add(
            Pet.objects.create(name="Socks"),
            Pet.objects.create(name="Coffee"),
        )

        with self.assertNumQueries(2):
            person = Person.objects.prefetch_related("pets").get(name="Bella")
        with self.assertNumQueries(0):
            self.assertEqual(2, len(person.pets.all()))