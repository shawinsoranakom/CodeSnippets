def test_add_related_null(self):
        nulldriver = Driver.objects.create(name=None)
        msg = 'Cannot add "<Driver: None>": the value for field "driver" is None'
        with self.assertRaisesMessage(ValueError, msg):
            self.car.drivers._add_items("car", "driver", nulldriver)