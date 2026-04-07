def test_prefetch_related_from_uuid_model_to_uuid_model_with_values_flat(self):
        pet = Pet.objects.create(name="Fifi")
        pet.people.add(
            Person.objects.create(name="Ellen"),
            Person.objects.create(name="George"),
        )
        self.assertSequenceEqual(
            Pet.objects.prefetch_related("fleas_hosted").values_list("id", flat=True),
            [pet.id],
        )