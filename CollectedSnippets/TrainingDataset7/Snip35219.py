def test_repeated_values(self):
        """
        assertQuerySetEqual checks the number of appearance of each item
        when used with option ordered=False.
        """
        batmobile = Car.objects.create(name="Batmobile")
        k2000 = Car.objects.create(name="K 2000")
        PossessedCar.objects.bulk_create(
            [
                PossessedCar(car=batmobile, belongs_to=self.p1),
                PossessedCar(car=batmobile, belongs_to=self.p1),
                PossessedCar(car=k2000, belongs_to=self.p1),
                PossessedCar(car=k2000, belongs_to=self.p1),
                PossessedCar(car=k2000, belongs_to=self.p1),
                PossessedCar(car=k2000, belongs_to=self.p1),
            ]
        )
        with self.assertRaises(AssertionError):
            self.assertQuerySetEqual(
                self.p1.cars.all(), [batmobile, k2000], ordered=False
            )
        self.assertQuerySetEqual(
            self.p1.cars.all(), [batmobile] * 2 + [k2000] * 4, ordered=False
        )