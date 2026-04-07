def setUpTestData(cls):
        cls.car = Car.objects.create(make="Toyota")
        cls.driver = Driver.objects.create(name="Ryan Briscoe")
        CarDriver.objects.create(car=cls.car, driver=cls.driver)
        # We are testing if wrong objects get deleted due to using wrong
        # field value in m2m queries. So, it is essential that the pk
        # numberings do not match.
        # Create one intentionally unused driver to mix up the autonumbering
        cls.unused_driver = Driver.objects.create(name="Barney Gumble")
        # And two intentionally unused cars.
        cls.unused_car1 = Car.objects.create(make="Trabant")
        cls.unused_car2 = Car.objects.create(make="Wartburg")