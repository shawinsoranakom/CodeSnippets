def test_use_explicit_o2o_to_parent_from_abstract_model(self):
        self.assertEqual(ParkingLot4A._meta.pk.name, "parent")
        ParkingLot4A.objects.create(
            name="Parking4A",
            address="21 Jump Street",
        )

        self.assertEqual(ParkingLot4B._meta.pk.name, "parent")
        ParkingLot4A.objects.create(
            name="Parking4B",
            address="21 Jump Street",
        )