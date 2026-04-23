def test_to_field_clear_reverse(self):
        self.driver.car_set.clear()
        self.assertSequenceEqual(self.driver.car_set.all(), [])