def test_add_null_reverse_related(self):
        nulldriver = Driver.objects.create(name=None)
        msg = (
            '"<Driver: None>" needs to have a value for field "name" before '
            "this many-to-many relationship can be used."
        )
        with self.assertRaisesMessage(ValueError, msg):
            nulldriver.car_set._add_items("driver", "car", self.car)