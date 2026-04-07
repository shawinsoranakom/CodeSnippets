def test_remove(self):
        self.assertSequenceEqual(self.car.drivers.all(), [self.driver])
        self.car.drivers._remove_items("car", "driver", self.driver)
        self.assertSequenceEqual(self.car.drivers.all(), [])