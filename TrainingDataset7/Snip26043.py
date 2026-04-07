def test_add_null_reverse(self):
        nullcar = Car.objects.create(make=None)
        msg = 'Cannot add "<Car: None>": the value for field "car" is None'
        with self.assertRaisesMessage(ValueError, msg):
            self.driver.car_set._add_items("driver", "car", nullcar)