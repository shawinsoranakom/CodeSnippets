def test_add_reverse(self):
        car2 = Car.objects.create(make="Honda")
        self.assertCountEqual(self.driver.car_set.all(), [self.car])
        self.driver.car_set._add_items("driver", "car", car2)
        self.assertCountEqual(self.driver.car_set.all(), [self.car, car2])