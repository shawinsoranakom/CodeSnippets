def test_add(self):
        self.assertSequenceEqual(self.car.drivers.all(), [self.driver])
        # Yikes - barney is going to drive...
        self.car.drivers._add_items("car", "driver", self.unused_driver)
        self.assertSequenceEqual(
            self.car.drivers.all(),
            [self.unused_driver, self.driver],
        )