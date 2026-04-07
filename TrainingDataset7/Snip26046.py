def test_remove_reverse(self):
        self.assertSequenceEqual(self.driver.car_set.all(), [self.car])
        self.driver.car_set._remove_items("driver", "car", self.car)
        self.assertSequenceEqual(self.driver.car_set.all(), [])