def test_managers(self):
        # Each model class gets a "_default_manager" attribute, which is a
        # reference to the first manager defined in the class.
        Car.cars.create(name="Corvette", mileage=21, top_speed=180)
        Car.cars.create(name="Neon", mileage=31, top_speed=100)

        self.assertQuerySetEqual(
            Car._default_manager.order_by("name"),
            [
                "Corvette",
                "Neon",
            ],
            lambda c: c.name,
        )
        self.assertQuerySetEqual(
            Car.cars.order_by("name"),
            [
                "Corvette",
                "Neon",
            ],
            lambda c: c.name,
        )
        # alternate manager
        self.assertQuerySetEqual(
            Car.fast_cars.all(),
            [
                "Corvette",
            ],
            lambda c: c.name,
        )
        # explicit default manager
        self.assertQuerySetEqual(
            FastCarAsDefault.cars.order_by("name"),
            [
                "Corvette",
                "Neon",
            ],
            lambda c: c.name,
        )
        self.assertQuerySetEqual(
            FastCarAsDefault._default_manager.all(),
            [
                "Corvette",
            ],
            lambda c: c.name,
        )
        # explicit base manager
        self.assertQuerySetEqual(
            FastCarAsBase.cars.order_by("name"),
            [
                "Corvette",
                "Neon",
            ],
            lambda c: c.name,
        )
        self.assertQuerySetEqual(
            FastCarAsBase._base_manager.all(),
            [
                "Corvette",
            ],
            lambda c: c.name,
        )