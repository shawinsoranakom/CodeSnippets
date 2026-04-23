def test_to_field_clear(self):
        self.car.drivers.clear()
        self.assertSequenceEqual(self.car.drivers.all(), [])