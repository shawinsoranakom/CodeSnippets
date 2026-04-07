def test_related_null_to_field_related_managers(self):
        car = Car.objects.create(make=None)
        driver = Driver.objects.create()
        msg = (
            f'"{car!r}" needs to have a value for field "make" before this '
            f"relationship can be used."
        )
        with self.assertRaisesMessage(ValueError, msg):
            car.drivers.add(driver)
        with self.assertRaisesMessage(ValueError, msg):
            car.drivers.create()
        with self.assertRaisesMessage(ValueError, msg):
            car.drivers.get_or_create()
        with self.assertRaisesMessage(ValueError, msg):
            car.drivers.update_or_create()
        with self.assertRaisesMessage(ValueError, msg):
            car.drivers.remove(driver)
        with self.assertRaisesMessage(ValueError, msg):
            car.drivers.clear()
        with self.assertRaisesMessage(ValueError, msg):
            car.drivers.set([driver])

        with self.assertNumQueries(0):
            self.assertEqual(car.drivers.count(), 0)